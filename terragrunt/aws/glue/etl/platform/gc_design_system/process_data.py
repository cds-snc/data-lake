import json
import os
import sys
import zipfile

from datetime import datetime, timedelta, timezone
from typing import List

import boto3

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql.functions import (
    coalesce,
    col,
    count,
    lit,
    lower,
    regexp_extract,
    sum as spark_sum,
    trim,
    when,
)

import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "source_bucket",
        "source_prefix",
        "output_bucket",
        "output_prefix",
        "database_name_output",
        "table_config_object",
        "table_name_prefix",
        "target_env",
        "gx_config_object",
    ],
)

JOB_NAME = args["JOB_NAME"]
SOURCE_BUCKET = args["source_bucket"]
SOURCE_PREFIX = args["source_prefix"]
OUTPUT_BUCKET = args["output_bucket"]
OUTPUT_PREFIX = args["output_prefix"]
OUTPUT_PATH = f"s3://{OUTPUT_BUCKET}/{OUTPUT_PREFIX}"
DATABASE_NAME_OUTPUT = args["database_name_output"]
TABLE_CONFIG_OBJECT = args["table_config_object"]
TABLE_NAME_PREFIX = args["table_name_prefix"]
TARGET_ENV = args["target_env"]
GX_CONFIG_OBJECT = args["gx_config_object"]

DEV_REFERRER_HOSTS = ["localhost", "127.0.0.1", "host.docker.internal"]
DEV_REFERRER_SUFFIX = ".ddev.site"

REFERRER_HOST_REGEX = r"^[A-Za-z][A-Za-z0-9+.-]*://([^/:?#]+)"

NO_REFERRER = "(none)"
UNKNOWN_REFERRER = "(unknown)"

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

if spark is not None:
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

logger = glueContext.get_logger()


def load_expectation_suite(suite_name: str) -> ExpectationSuite:
    """
    Load a Great Expectations suite from the JSON files shipped in the gx
    configuration archive (gx/expectations/<suite_name>.json).
    """
    suite_path = os.path.join(os.getcwd(), "gx", "expectations", f"{suite_name}.json")
    with open(suite_path, "r") as f:
        suite_config = json.load(f)

    return ExpectationSuite(
        name=suite_config["name"],
        expectations=[
            ExpectationConfiguration(
                type=expectation["type"],
                kwargs=expectation["kwargs"],
                meta=expectation.get("meta", {}),
            )
            for expectation in suite_config["expectations"]
        ],
    )


def store_validation_result(result, suite_name: str, target_gx_bucket: str) -> None:
    """
    Write the Great Expectations validation result to S3.  Great Expectations 1.x
    no longer ships an S3 store backend, so the result is written directly.
    A failure to store the result never fails the validation itself.
    """
    if "test" in target_gx_bucket:
        logger.info("Not writing validation result to S3 (test bucket)")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    key = (
        "platform/gc-design-system/data-validation/validations/"
        f"{suite_name}/{timestamp}.json"
    )
    try:
        boto3.client("s3").put_object(
            Bucket=target_gx_bucket,
            Key=key,
            Body=json.dumps(result.to_json_dict(), default=str).encode("utf-8"),
        )
        logger.info(f"Validation result written to s3://{target_gx_bucket}/{key}")
    except Exception as e:
        logger.warn(f"Could not write validation result to S3: {str(e)}")


def validate_with_gx(
    dataframe: SparkDataFrame,
    suite_name: str,
    batch_name: str = "runtime_batch",
) -> bool:
    """
    Validate the Spark DataFrame using the specified Great Expectations suite.
    Logs the details of every failed expectation.

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        suite = load_expectation_suite(suite_name)

        context = gx.get_context(mode="ephemeral")
        data_source = context.data_sources.add_spark(name="spark_datasource")
        data_asset = data_source.add_dataframe_asset(name=suite_name)
        batch_definition = data_asset.add_batch_definition_whole_dataframe(batch_name)
        suite = context.suites.add(suite)
        validation_definition = context.validation_definitions.add(
            gx.ValidationDefinition(
                name=f"{suite_name}_validation", data=batch_definition, suite=suite
            )
        )

        result = validation_definition.run(batch_parameters={"dataframe": dataframe})

        store_validation_result(result, suite_name, OUTPUT_BUCKET)

        if not result.success:
            logger.error(f"Validation failed for suite '{suite_name}'")

            for res in result.results:
                if res.success:
                    continue
                config = res.expectation_config
                details = res.result or {}
                logger.error(
                    f"FAILED: {config.type} "
                    f"on column '{config.kwargs.get('column', '')}'"
                )
                logger.error(f"Expected: {config.kwargs}")
                for key in (
                    "partial_unexpected_list",
                    "unexpected_count",
                    "element_count",
                    "observed_value",
                ):
                    if key in details:
                        logger.error(f"{key}: {details[key]}")
                logger.error("=" * 80)
            return False

        logger.info(f"Validation succeeded for suite '{suite_name}'.")
        return True
    except Exception as e:
        logger.error(f"Error during Great Expectations validation: {str(e)}")
        return False


def get_date_from(look_back_days: int, today: datetime = None) -> str:
    """
    Return the first date (YYYY-MM-DD, UTC) of the re-processing window.  CloudFront
    log files can be delivered after midnight, so the most recent days are always
    re-processed and their partitions overwritten.

    Unlike GC Notify, which reloads from the start of the month because it overwrites
    month partitions, this table is partitioned by date so only a few days are
    re-read each run instead of a whole month of request-level logs.
    """
    today = today or datetime.now(timezone.utc)
    return (today - timedelta(days=look_back_days)).strftime("%Y-%m-%d")


def read_cloudfront_logs(date_from: str) -> SparkDataFrame:
    """
    Read the CloudFront log Parquet files from the date partitions on or after date_from.
    """
    source_path = f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/"
    logger.info(f"Reading {source_path} from {date_from}...")

    df = spark.read.parquet(source_path)
    df = df.withColumn("date", col("date").cast("string"))
    return df.filter(col("date") >= lit(date_from))


def aggregate_cloudfront_logs(df: SparkDataFrame) -> SparkDataFrame:
    """
    Aggregate raw CloudFront request logs to one row per date, referrer host,
    host, URI, status and cache result with the request and byte counts.
    """
    referer = trim(col("`cs(referer)`"))
    referer_host = lower(regexp_extract(referer, REFERRER_HOST_REGEX, 1))

    referrer_host = (
        when(referer.isNull() | (referer == "") | (referer == "-"), lit(NO_REFERRER))
        .when(referer_host != "", referer_host)
        .otherwise(lit(UNKNOWN_REFERRER))
    )

    is_dev_traffic = referrer_host.isin(DEV_REFERRER_HOSTS) | referrer_host.endswith(
        DEV_REFERRER_SUFFIX
    )

    return (
        df.select(
            col("date"),
            referrer_host.alias("referrer_host"),
            is_dev_traffic.alias("is_dev_traffic"),
            col("`cs(host)`").alias("distribution_domain"),
            col("`x-host-header`").alias("host_header"),
            col("`cs-uri-stem`").alias("uri_stem"),
            col("`sc-status`").alias("status"),
            col("`x-edge-result-type`").alias("edge_result_type"),
            col("`sc-bytes`").cast("long").alias("bytes"),
        )
        .groupBy(
            "referrer_host",
            "is_dev_traffic",
            "distribution_domain",
            "host_header",
            "uri_stem",
            "status",
            "edge_result_type",
            "date",
        )
        .agg(
            count(lit(1)).alias("requests"),
            coalesce(spark_sum("bytes"), lit(0)).alias("bytes_sent"),
        )
    )


def get_dataset_config() -> List[dict]:
    datasets = []
    tables_dir = os.path.join(os.getcwd(), "tables")

    try:
        for filename in sorted(os.listdir(tables_dir)):
            if filename.endswith(".json"):
                file_path = os.path.join(tables_dir, filename)
                logger.info(f"Loading dataset configuration from {file_path}")
                with open(file_path, "r") as f:
                    datasets.append(json.load(f))
    except FileNotFoundError:
        raise ValueError(
            "Tables directory not found. Please create it and add dataset configuration files."
        )

    if not datasets:
        raise ValueError("No dataset configurations found.")

    logger.info(f"Loaded {len(datasets)} dataset configurations")
    return datasets


def download_s3_object(s3: boto3.client, s3_url: str, filename: str) -> None:
    """
    Download a zip file from S3 and extract it to a folder named after the file.
    """
    bucket_name = s3_url.split("/")[2]
    object_key = "/".join(s3_url.split("/")[3:])
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, filename)

    s3.download_file(Bucket=bucket_name, Key=object_key, Filename=file_path)

    folder_path = os.path.join(current_dir, filename.split(".")[0])
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(folder_path)


def register_table(df: SparkDataFrame, table: str, location: str, partition_cols):
    """
    Recreate the partitioned table in the Glue Data Catalog and load the partitions.
    The table is dropped first, as in GC Notify, so the catalog schema never drifts
    from the data.  It is an external table, so the data in S3 is not deleted.
    """
    columns = ", ".join(f"`{f.name}` {f.dataType.simpleString()}" for f in df.schema)
    partitions = ", ".join(f"`{c}`" for c in partition_cols)
    full_name = f"{DATABASE_NAME_OUTPUT}.{table}"

    spark.sql(f"DROP TABLE IF EXISTS {full_name}")

    create_sql = f"""
        CREATE TABLE {full_name} ({columns})
        USING PARQUET
        PARTITIONED BY ({partitions})
        LOCATION '{location}'
    """
    logger.info(f"Registering Glue table with SQL: {create_sql}")
    spark.sql(create_sql)
    spark.sql(f"MSCK REPAIR TABLE {full_name}")
    logger.info(f"Catalog table: {full_name}")


def process_data():
    """
    Read the CloudFront logs, aggregate them, validate the result and write it
    back to S3 as a partitioned table.
    """
    s3 = boto3.client("s3")

    download_s3_object(s3, TABLE_CONFIG_OBJECT, "tables.zip")
    download_s3_object(s3, GX_CONFIG_OBJECT, "gx.zip")

    for dataset in get_dataset_config():
        table_name = dataset["table_name"]
        partition_cols = dataset["partition_cols"]
        look_back_days = dataset["look_back_days"]
        gx_suite = f"gcds-{table_name}_suite"

        logger.info(f"Processing {table_name} data...")
        data = aggregate_cloudfront_logs(
            read_cloudfront_logs(get_date_from(look_back_days))
        ).cache()

        row_count = data.count()

        if not validate_with_gx(data, gx_suite):
            raise ValueError(
                f"Great Expectations validation failed for {table_name}. Aborting ETL process."
            )

        table = f"{TABLE_NAME_PREFIX}_{table_name}"
        s3_output_path = f"{OUTPUT_PATH}/{table_name}/"

        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
        data.write.mode("overwrite").partitionBy(partition_cols).parquet(s3_output_path)
        logger.info(f"Wrote {row_count} rows to {s3_output_path}")

        register_table(data, table, s3_output_path, partition_cols)
        data.unpersist()

    logger.info("ETL process completed successfully.")


if __name__ == "__main__":
    job = Job(glueContext)
    job.init(JOB_NAME, args)
    process_data()
    job.commit()
