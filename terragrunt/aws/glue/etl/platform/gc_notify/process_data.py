import json
import os
import sys
import zipfile

from datetime import datetime, timedelta
from typing import List, TypedDict

import boto3

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from awsglue.dynamicframe import DynamicFrame
from pyspark.context import SparkContext
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql.functions import (
    col,
    date_format,
    year,
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
    BooleanType,
    TimestampType,
)

import great_expectations as gx


args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "source_bucket",
        "source_prefix",
        "transformed_bucket",
        "transformed_prefix",
        "database_name_transformed",
        "table_config_object",
        "table_name_prefix",
        "target_env",
        "gx_config_object",
    ],
)

JOB_NAME = args["JOB_NAME"]
SOURCE_BUCKET = args["source_bucket"]
SOURCE_PREFIX = args["source_prefix"]
TRANSFORMED_BUCKET = args["transformed_bucket"]
TRANSFORMED_PREFIX = args["transformed_prefix"]
TRANSFORMED_PATH = f"s3://{TRANSFORMED_BUCKET}/{TRANSFORMED_PREFIX}"
DATABASE_NAME_TRANSFORMED = args["database_name_transformed"]
TABLE_CONFIG_OBJECT = args["table_config_object"]
TABLE_NAME_PREFIX = args["table_name_prefix"]
TARGET_ENV = args["target_env"]
GX_CONFIG_OBJECT = args["gx_config_object"]


# Initialize Spark and Glue contexts
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Configure Spark to handle timestamp parsing issues with Spark 3.0+
if spark is not None:
    spark.conf.set("spark.sql.legacy.timeParserPolicy", "LEGACY")
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

logger = glueContext.get_logger()


class Field(TypedDict):
    name: str
    type: str


def configure_gx_stores(context: gx.DataContext, target_gx_bucket: str = None):
    """
    Properly configure all Great Expectations stores to use S3 at runtime.
    This uses context.add_store to ensure the stores are actually registered.
    """
    if "test" not in target_gx_bucket:
        logger.info(f"Writing to S3 bucket: {target_gx_bucket}")

        context.add_store(
            store_name="validations_store",
            store_config={
                "class_name": "ValidationsStore",
                "store_backend": {
                    "class_name": "TupleS3StoreBackend",
                    "bucket": target_gx_bucket,
                    "prefix": "platform/gc-notify/data-validation/validations/",
                },
            },
        )

        context.add_store(
            store_name="evaluation_parameter_store",
            store_config={
                "class_name": "EvaluationParameterStore",
            },
        )
    else:
        logger.info("Writing Locally")


def validate_with_gx(
    dataframe: SparkDataFrame,
    spark_session,
    checkpoint_name: str,
    batch_name: str = "runtime_batch",
) -> bool:
    """
    Validate the Spark DataFrame using the specified Great Expectations checkpoint.
    Uses Spark DataFrames natively with Great Expectations.
    Logs detailed errors if validation fails.

    Args:
        dataframe: Spark DataFrame to validate
        spark_session: Spark session to use for validation
        checkpoint_name: Name of the GX checkpoint to run
        batch_name: Name for the batch identifier

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        gx_context_path = os.path.join(os.getcwd(), "gx")
        context = gx.get_context(context_root_dir=gx_context_path, cloud_mode=False)

        configure_gx_stores(context, SOURCE_BUCKET)

        # Ensure Great Expectations uses the provided Spark session
        # This is important for Spark DataFrame validation
        context.datasources["spark_datasource"].execution_engine.spark = spark_session

        # Use Spark DataFrame directly with Great Expectations
        result = context.run_checkpoint(
            checkpoint_name=checkpoint_name,
            batch_request={
                "runtime_parameters": {"batch_data": dataframe},
                "batch_identifiers": {"default_identifier_name": batch_name},
            },
        )

        if not result["success"]:
            logger.error(f"Validation failed for checkpoint '{checkpoint_name}'")

            # Print detailed failed expectations with actual values
            for run_result in result["run_results"].values():
                validation_result = run_result["validation_result"]
                for res in validation_result["results"]:
                    if not res["success"]:
                        expectation_type = res["expectation_config"]["expectation_type"]
                        expectation_definition = res["expectation_config"]["kwargs"]
                        column = expectation_definition.get("column", "")
                        result_details = res.get("result", {})

                        # Log basic failure info
                        logger.error(f"FAILED: {expectation_type} on column '{column}'")
                        logger.error(f"Expected: {expectation_definition}")

                        # Extract and log specific failure details
                        if "partial_unexpected_list" in result_details:
                            unexpected_values = result_details[
                                "partial_unexpected_list"
                            ]
                            logger.error(f"Sample failing values: {unexpected_values}")

                        if "unexpected_count" in result_details:
                            unexpected_count = result_details["unexpected_count"]
                            total_count = result_details.get("element_count", "unknown")
                            logger.error(
                                f"Failed rows: {unexpected_count} out of {total_count}"
                            )

                        if "observed_value" in result_details:
                            observed = result_details["observed_value"]
                            logger.error(f"Observed value: {observed}")

                        # For regex failures, show actual vs expected pattern
                        if expectation_type == "expect_column_values_to_match_regex":
                            regex_pattern = expectation_definition.get("regex", "")
                            logger.error(f"Regex pattern that failed: {regex_pattern}")

                            # Get sample of actual values that failed - simple approach
                            if column and column in dataframe.columns:
                                try:
                                    # Just get a few sample values as strings
                                    samples = (
                                        dataframe.select(
                                            col(column).cast("string").alias("sample")
                                        )
                                        .limit(5)
                                        .collect()
                                    )
                                    sample_values = [row["sample"] for row in samples]
                                    logger.error(
                                        f"Sample values in column '{column}': {sample_values}"
                                    )
                                except Exception as sample_error:
                                    logger.error(
                                        f"Could not sample column: {sample_error}"
                                    )

                        # For range/between failures, show min/max values
                        if expectation_type == "expect_column_values_to_be_between":
                            min_val = expectation_definition.get("min_value")
                            max_val = expectation_definition.get("max_value")
                            logger.error(f"Expected range: {min_val} to {max_val}")

                            if column and column in dataframe.columns:
                                try:
                                    stats = (
                                        dataframe.select(column)
                                        .summary("min", "max", "count")
                                        .collect()
                                    )
                                    for stat in stats:
                                        logger.error(
                                            f"Actual {stat['summary']}: {stat[column]}"
                                        )
                                except Exception as stats_error:
                                    logger.error(
                                        f"Could not get column stats: {stats_error}"
                                    )

                        # For set membership failures, show what values were found
                        if expectation_type == "expect_column_values_to_be_in_set":
                            expected_set = expectation_definition.get("value_set", [])
                            logger.error(f"Expected values: {expected_set}")

                            if column and column in dataframe.columns:
                                try:
                                    distinct_values = (
                                        dataframe.select(column)
                                        .distinct()
                                        .limit(20)
                                        .collect()
                                    )
                                    actual_values = [
                                        row[column] for row in distinct_values
                                    ]
                                    logger.error(
                                        f"Actual distinct values in column '{column}': {actual_values}"
                                    )
                                except Exception as distinct_error:
                                    logger.error(
                                        f"Could not get distinct values: {distinct_error}"
                                    )

                        logger.error("=" * 80)  # Separator between failures
            return False
        logger.info(f"Validation succeeded for checkpoint '{checkpoint_name}'.")
        return True
    except Exception as e:
        logger.error(f"Error during Great Expectations validation: {str(e)}")
        return False


def postgres_to_spark_type(field_type: str):
    """
    Convert PostgreSQL data types to Spark data types.
    """
    postgres_to_spark = {
        "notification_feedback_types": StringType(),
        "notification_feedback_subtypes": StringType(),
        "notification_type": StringType(),
        "permission_types": StringType(),
        "sms_sending_vehicle": StringType(),
        "template_type": StringType(),
        "uuid": StringType(),
        "varchar": StringType(),
        "text": StringType(),
        "int": IntegerType(),
        "integer": IntegerType(),
        "numeric": DoubleType(),
        "float": DoubleType(),
        "bool": BooleanType(),
        "boolean": BooleanType(),
        "timestamp": TimestampType(),
    }
    return postgres_to_spark.get(field_type, StringType())


def create_schema_from_fields(fields: List[Field]) -> StructType:
    """
    Create a Spark StructType schema from the dataset field configuration.
    This eliminates the need for schema inference by using the explicit
    field definitions from the JSON configuration files.

    Args:
        fields: List of field definitions with name and type

    Returns:
        StructType: Spark schema ready for DataFrame operations
    """
    schema_fields = []
    for field in fields:
        field_name = field["name"]
        spark_type = postgres_to_spark_type(field["type"])
        schema_fields.append(StructField(field_name, spark_type, True))

    schema = StructType(schema_fields)
    logger.info(
        f"Created schema with {len(fields)} fields: {[f.name for f in schema_fields]}"
    )
    return schema


def get_new_data(
    path: str,
    fields: List[Field],
    partition_timestamp: str = None,
    partition_cols: List[str] = None,
    date_from: str = None,
) -> SparkDataFrame:
    """
    Reads the data from the specified path in S3 and returns a Spark DataFrame.
    Uses the provided fields configuration to create an explicit schema,
    avoiding schema inference issues entirely.
    """
    field_names = [field["name"] for field in fields]
    s3_path = f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/{path}/*"

    # Create schema for fallback in case of errors
    fallback_schema = StructType(
        [
            StructField(field["name"], postgres_to_spark_type(field["type"]), True)
            for field in fields
        ]
    )

    try:
        logger.info(f"Reading {s3_path} data from S3 with explicit schema...")

        # Read data using explicit schema - no inference needed
        df = spark.read.parquet(s3_path)

        logger.info("Successfully read data with explicit schema from configuration")

        # Apply date filtering after reading
        if date_from and partition_timestamp and partition_timestamp in df.columns:
            logger.info(f"Applying incremental filter from {date_from}...")
            df = df.filter(col(partition_timestamp) >= date_from)

        # Select only the required columns (they should all exist with explicit schema)
        existing_columns = df.columns
        available_fields = [field for field in field_names if field in existing_columns]

        if len(available_fields) != len(field_names):
            missing_fields = [
                field for field in field_names if field not in existing_columns
            ]
            logger.warning(f"Some configured fields missing in data: {missing_fields}")
            logger.info(f"Available columns: {existing_columns}")

        # Filter df to only include the specified fields
        df = df.select(available_fields)

        # Apply schema transformations for proper data types
        for field in fields:
            field_name = field["name"]
            if field_name not in df.columns:
                logger.warning(
                    f"Skipping transformation for missing field: {field_name}"
                )
                continue

            field_type = postgres_to_spark_type(field["type"])

            df = df.withColumn(field_name, col(field_name).cast(field_type))

        # Add partition columns if specified
        if partition_timestamp and partition_cols and partition_timestamp in df.columns:
            timestamp_col = col(partition_timestamp)
            for partition in partition_cols:
                if partition == "year":
                    df = df.withColumn("year", year(timestamp_col).cast(StringType()))
                elif partition == "month":
                    df = df.withColumn("month", date_format(timestamp_col, "yyyy-MM"))
                elif partition == "day":
                    df = df.withColumn("day", date_format(timestamp_col, "yyyy-MM-dd"))

        row_count = df.count()
        logger.info(f"Successfully processed {row_count} records")
        return df

    except Exception as e:
        logger.error(f"Error reading {path} data: {str(e)}")

        # Log the schema we attempted to use for debugging
        logger.error(f"Attempted to read with fallback schema: {fallback_schema}")

        # Return empty DataFrame with the same explicit schema
        logger.warning("Returning empty DataFrame due to read failure")
        return spark.createDataFrame([], fallback_schema)


def get_dataset_config():
    datasets = []

    current_dir = os.getcwd()
    tables_dir = os.path.join(current_dir, "tables")

    try:
        for filename in os.listdir(tables_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(tables_dir, filename)
                logger.info(f"Loading dataset configuration from {file_path}")
                try:
                    with open(file_path, "r") as f:
                        dataset_config = json.load(f)
                        datasets.append(dataset_config)
                        logger.info(
                            f"Added dataset configuration for {dataset_config.get('table_name', 'unknown')}"
                        )
                except (json.JSONDecodeError, IOError) as e:
                    logger.error(
                        f"Error reading dataset configuration from {file_path}: {str(e)}"
                    )
    except FileNotFoundError:
        logger.error(f"Tables directory not found at {tables_dir}")
        raise ValueError(
            "Tables directory not found. Please create it and add dataset configuration files."
        )

    if not datasets:
        logger.error(
            "No dataset configurations found. Please add .json files to the tables directory."
        )
        raise ValueError("No dataset configurations found.")

    logger.info(f"Loaded {len(datasets)} dataset configurations")
    return datasets


def download_s3_object(s3: boto3.client, s3_url: str, filename: str) -> None:
    """
    Download an S3 object to a local file.
    """
    bucket_name = s3_url.split("/")[2]
    object_key = "/".join(s3_url.split("/")[3:])
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, filename)

    s3.download_file(
        Bucket=bucket_name,
        Key=object_key,
        Filename=file_path,
    )

    folder_path = os.path.join(current_dir, filename.split(".")[0])

    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(folder_path)


def get_incremental_load_date_from(data_look_back_days: int) -> str:
    """
    Get the date from which to load incremental data.  This will always be the beginning of
    the month that is today minus the look back days.  The reason for this is because we
    perform a month partition overwrite and need to make sure that we are loading
    all data within the overwritten month partition(s) while respecting the data retention policy.
    """
    today = datetime.now()
    month_start = (today - timedelta(days=data_look_back_days)).replace(day=1)
    return month_start.strftime("%Y-%m-%d %H:%M:%S")


def process_data():
    """
    Main ETL process to read data from S3, validate the schema, and save the
    transformed data back to S3.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    path_prefix = f"notification-canada-ca-{TARGET_ENV}-cluster-{today}/NotificationCanadaCa{TARGET_ENV}/public."
    s3 = boto3.client("s3")

    # Download the table configuration file from S3
    download_s3_object(s3, TABLE_CONFIG_OBJECT, "tables.zip")

    # Download the Great Expectations configuration from S3
    download_s3_object(s3, GX_CONFIG_OBJECT, "gx.zip")

    # Read the dataset configuration and start processing
    datasets = get_dataset_config()
    for dataset in datasets:
        table_name = dataset.get("table_name")
        path = f"{path_prefix}{table_name}"
        partition_cols = dataset.get("partition_cols")
        incremental_load = dataset.get("incremental_load", False)
        look_back_days = dataset.get("look_back_days", 0)
        gx_checkpoint = f"notify-{table_name}_checkpoint"

        # Retrieve the new data using Spark
        logger.info(f"Processing {table_name} data...")
        data = get_new_data(
            path,
            dataset.get("fields"),
            dataset.get("partition_timestamp"),
            partition_cols,
            date_from=(
                get_incremental_load_date_from(look_back_days)
                if incremental_load
                else None
            ),
        )

        row_count = data.count()
        if row_count > 0:
            if not validate_with_gx(data, spark, gx_checkpoint):
                raise ValueError(
                    f"Great Expectations validation failed for {table_name}. Aborting ETL process."
                )

            # Save the transformed data back to S3 using Spark
            logger.info(f"Saving new {table_name} DataFrame to S3...")
            table = f"{TABLE_NAME_PREFIX}_{table_name}"

            # Convert Spark DataFrame to Glue DynamicFrame for native integration
            dynamic_frame = DynamicFrame.fromDF(data, glueContext, table)

            # Convert DynamicFrame to Spark DataFrame
            spark_df = dynamic_frame.toDF()

            # Explicitly set dynamic partition overwrite mode before writing
            spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

            # Write the DataFrame to S3 using Spark's write method with dynamic partition overwrite
            s3_output_path = f"{TRANSFORMED_PATH}/{table_name}/"

            # If not incremental, delete all objects under the output path to remove old partitions
            if not incremental_load:
                logger.info(
                    f"Deleting all objects under {s3_output_path} before full overwrite..."
                )
                s3_resource = boto3.resource("s3")
                bucket = s3_resource.Bucket(TRANSFORMED_BUCKET)
                prefix = f"{TRANSFORMED_PREFIX}/{table_name}/"
                delete_objs = bucket.objects.filter(Prefix=prefix)
                deleted = [obj.delete() for obj in delete_objs]
                logger.info(f"Deleted {len(deleted)} objects from {s3_output_path}")

            if partition_cols:
                spark_df.write.mode("overwrite").partitionBy(partition_cols).parquet(
                    s3_output_path
                )
            else:
                spark_df.write.mode("overwrite").parquet(s3_output_path)

            logger.info(
                f"Successfully wrote {row_count} records to {s3_output_path} using Spark DataFrame write."
            )
            logger.info(f"Data written with partitions: {partition_cols}")
            logger.info(f"Catalog table: {DATABASE_NAME_TRANSFORMED}.{table}")

            # Register table in Glue Data Catalog - only for partitioned tables
            if partition_cols:
                # Drop table if exists to avoid schema drift
                spark.sql(f"DROP TABLE IF EXISTS {DATABASE_NAME_TRANSFORMED}.{table}")

                # Create a temp view from the DataFrame for registration
                spark_df.limit(0).createOrReplaceTempView("temp_table_for_registration")

                partition_str = ", ".join(partition_cols)
                create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {DATABASE_NAME_TRANSFORMED}.{table}
                    USING PARQUET
                    LOCATION '{s3_output_path}'
                    PARTITIONED BY ({partition_str})
                    AS SELECT * FROM temp_table_for_registration WHERE 1=0
                """
                logger.info(
                    f"Registering partitioned Glue table with SQL: {create_sql}"
                )
                spark.sql(create_sql)

                # Refresh partitions to ensure Glue knows about the new partitions
                try:
                    logger.info(
                        f"Running MSCK REPAIR TABLE to discover partitions for {DATABASE_NAME_TRANSFORMED}.{table}"
                    )
                    spark.sql(f"MSCK REPAIR TABLE {DATABASE_NAME_TRANSFORMED}.{table}")
                    logger.info(
                        f"Successfully refreshed partitions for {DATABASE_NAME_TRANSFORMED}.{table}"
                    )
                except Exception as repair_e:
                    logger.warning(
                        f"MSCK REPAIR failed (table might not exist yet): {str(repair_e)}"
                    )
            else:
                # For unpartitioned tables, create table directly pointing to the data
                spark.sql(f"DROP TABLE IF EXISTS {DATABASE_NAME_TRANSFORMED}.{table}")
                create_sql = f"""
                    CREATE TABLE {DATABASE_NAME_TRANSFORMED}.{table}
                    USING PARQUET
                    LOCATION '{s3_output_path}'
                """
                logger.info(
                    f"Registering unpartitioned Glue table with SQL: {create_sql}"
                )
                spark.sql(create_sql)

        else:
            logger.error(f"No new {table_name} data found.")

    logger.info("ETL process completed successfully.")


if __name__ == "__main__":
    job = Job(glueContext)
    job.init(JOB_NAME, args)
    process_data()
    job.commit()
