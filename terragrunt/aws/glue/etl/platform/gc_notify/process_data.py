import json
import os
import sys
import zipfile

from datetime import datetime, timedelta, timezone
from typing import List, TypedDict

import awswrangler as wr
import boto3
import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

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


# Anomaly detection configuration
METRIC_NAMESPACE = "data-lake/etl/gc-notify"
METRIC_NAME = "ProcessedRecordCount"
ANOMALY_LOOKBACK_DAYS = 14
ANOMALY_STANDARD_DEVIATION = 2.5

glueContext = GlueContext(SparkContext.getOrCreate())
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


def validate_with_gx(dataframe: pd.DataFrame, checkpoint_name: str) -> bool:
    """
    Validate the DataFrame using the specified Great Expectations checkpoint.
    Logs detailed errors if validation fails.
    """
    gx_context_path = os.path.join(os.getcwd(), "gx")
    context = gx.get_context(context_root_dir=gx_context_path, cloud_mode=False)

    configure_gx_stores(context, SOURCE_BUCKET)

    result = context.run_checkpoint(
        checkpoint_name=checkpoint_name,
        batch_request={
            "runtime_parameters": {"batch_data": dataframe},
            "batch_identifiers": {"default_identifier_name": "runtime_batch"},
        },
    )
    if not result["success"]:
        logger.error(f"Validation failed for checkpoint '{checkpoint_name}'")
        # Print detailed failed expectations
        for run_result in result["run_results"].values():
            validation_result = run_result["validation_result"]
            for res in validation_result["results"]:
                if not res["success"]:
                    expectation_type = res["expectation_config"]["expectation_type"]
                    expectation_definition = res["expectation_config"]["kwargs"]
                    column = expectation_definition.get("column", "")
                    result_details = res.get("result", {})
                    logger.error(
                        f"Failed expectation: {expectation_type} on column '{column}'. "
                        f"Expectation definition: {expectation_definition}"
                        f"Run details {result_details}"
                    )
        return False
    logger.info(f"Validation succeeded for checkpoint '{checkpoint_name}'.")
    return True


def postgres_to_pandas_type(field_type: str) -> str:
    """
    Convert PostgreSQL data types to pandas data types.
    """
    postgres_to_pandas = {
        "notification_feedback_types": pd.StringDtype(),
        "notification_feedback_subtypes": pd.StringDtype(),
        "notification_type": pd.StringDtype(),
        "permission_types": pd.StringDtype(),
        "sms_sending_vehicle": pd.StringDtype(),
        "template_type": pd.StringDtype(),
        "uuid": pd.StringDtype(),
        "varchar": pd.StringDtype(),
        "text": pd.StringDtype(),
        "int": pd.Int64Dtype(),
        "integer": pd.Int64Dtype(),
        "numeric": pd.Float64Dtype(),
        "float": pd.Float64Dtype(),
        "bool": pd.BooleanDtype(),
        "boolean": pd.BooleanDtype(),
        "timestamp": "datetime64[ns]",
    }
    return postgres_to_pandas.get(field_type)


def parse_dates(date_series):
    """
    Parse date strings into pandas datetime objects.
    Handles both standard and non-standard formats.
    """
    # Try standard format first with milliseconds
    result = pd.to_datetime(date_series, format="%Y-%m-%d %H:%M:%S.%f", errors="coerce")

    # Find rows that failed parsing
    mask = result.isna()
    if mask.any():
        result[mask] = pd.to_datetime(
            date_series[mask], format="%Y-%m-%d %H:%M:%S", errors="coerce"
        )

    return result


def get_new_data(
    path: str,
    fields: List[Field],
    partition_timestamp: str = None,
    partition_cols: List[str] = None,
    date_from: str = None,
) -> pd.DataFrame:
    """
    Reads the data from the specified path in S3 and returns a DataFrame.
    This method is responsible for ensuring the data types are correct.
    """
    data = pd.DataFrame()
    field_names = [field["name"] for field in fields]
    s3_path = f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/{path}/"

    try:
        logger.info(
            f"Reading s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/{path}/ data from S3..."
        )

        # Only get new data within the time range
        if date_from and partition_timestamp:
            logger.info(f"Incremental data load from {date_from}...")
            dataset = ds.dataset(s3_path, format="parquet")
            filter_expr = ds.field(partition_timestamp) >= date_from
            scanner = dataset.scanner(filter=filter_expr, columns=field_names)
            table = scanner.to_table()
            data = table.to_pandas()

        # Read all data
        else:
            logger.info("Full data load...")
            data = wr.s3.read_parquet(
                path=s3_path,
                use_threads=True,
                dataset=True,
                columns=field_names,
            )
        logger.info(f"Loaded {len(data)} new records")

        # Ensure all columns have the correct type
        for field in fields:
            field_name = field["name"]
            field_type = postgres_to_pandas_type(field["type"])
            # Make sure dates are parsed correctly with UTC timezone
            if field_type == "datetime64[ns]":
                data[field_name] = parse_dates(data[field_name])
                data[field_name] = data[field_name].dt.tz_localize(None)
            # Handles a bug with Pandas and object conversion to Float
            elif field_type == pd.Float64Dtype.name:
                data[field_name] = data[field_name].astype("string").astype(field_type)
            else:
                data[field_name] = data[field_name].astype(field_type)

        # Define partition columns
        if partition_timestamp and partition_cols:
            partition_format = {
                "day": "%Y-%m-%d",
                "month": "%Y-%m",
                "year": "%Y",
            }
            for partition in partition_cols:
                data[partition] = data[partition_timestamp].dt.strftime(
                    partition_format[partition]
                )

    except wr.exceptions.NoFilesFound:
        logger.error(f"No new {path} data found.")
    return data


def publish_metric(
    cloudwatch: boto3.client,
    metric_namespace: str,
    metric_name: str,
    dataset_name: str,
    metric_value: float,
) -> None:
    """
    Publish data processing metrics to CloudWatch
    """
    cloudwatch.put_metric_data(
        Namespace=metric_namespace,
        MetricData=[
            {
                "MetricName": metric_name,
                "Dimensions": [{"Name": "Dataset", "Value": dataset_name}],
                "Value": metric_value,
                "Timestamp": datetime.now(timezone.utc),
                "Unit": "Count",
            },
        ],
    )
    logger.info(
        f"Published metrics for {dataset_name}: {metric_value} records processed"
    )


def get_metrics(
    cloudwatch: boto3.client,
    metric_namespace: str,
    metric_name: str,
    dataset_name: str,
    days: int,
) -> np.ndarray:
    """
    Retrieve historical metrics from CloudWatch for a specific dataset.
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)

    try:
        response = cloudwatch.get_metric_statistics(
            Namespace=metric_namespace,
            MetricName=metric_name,
            Dimensions=[{"Name": "Dataset", "Value": dataset_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # 1 day
            Statistics=["Maximum"],
        )

        # Sort by timestamp and extract values
        datapoints = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])
        values = [point["Maximum"] for point in datapoints]
        metrics = np.array(values)

        logger.info(f"Retrieved {metrics} metrics for {dataset_name} from CloudWatch.")
        return metrics

    except Exception as e:
        logger.error(f"Error fetching CloudWatch metric data: {e}")
        return None


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


def detect_anomalies(
    row_count: int, historical_data: np.ndarray, standard_deviation_threshold: float
) -> bool:
    """
    Detect anomalies by checking if the latest value falls within
    a certain number of standard deviations from the mean.
    """
    if historical_data is None or len(historical_data) == 0:
        logger.error("No historical data available for anomaly detection.")
        return False

    mean = np.mean(historical_data)
    standard_deviation = np.std(historical_data, ddof=1)

    z_score = 0
    if standard_deviation != 0:
        z_score = (row_count - mean) / standard_deviation

    is_anomaly = abs(z_score) > standard_deviation_threshold
    if is_anomaly:
        logger.error(
            f"Anomaly: Latest value {row_count}, Mean: {mean:.2f}, "
            f"Standard dev.: {standard_deviation:.2f}, Z-score: {z_score:.2f}, "
            f"Historical data: {historical_data}"
        )
    return is_anomaly


def get_incremental_load_date_from(data_look_back_days: int) -> str:
    """
    Get the date from which to load incremental data.  This will always be the beginning of
    the month that is today minus the look back days.  The reason for this is because we
    perform a month partition overwrite and need to make sure that we are loading
    all data within the overwritten month partition(s) while respecting the data retention policy.
    """
    today = pd.Timestamp.now().normalize()
    month_start = (today - pd.DateOffset(days=data_look_back_days)).replace(day=1)
    return month_start.strftime("%Y-%m-%d %H:%M:%S")


def process_data():
    """
    Main ETL process to read data from S3, validate the schema, and save the
    transformed data back to S3.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    path_prefix = f"notification-canada-ca-{TARGET_ENV}-cluster-{today}/NotificationCanadaCa{TARGET_ENV}/public."
    cloudwatch = boto3.client("cloudwatch")
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

        # Retrieve the new data
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
        if not data.empty:
            if not validate_with_gx(data, gx_checkpoint):
                raise ValueError(
                    f"Great Expectations validation failed for {table_name}. Aborting ETL process."
                )

            # Save the transformed data back to S3
            logger.info(f"Saving new {table_name} DataFrame to S3...")
            table = f"{TABLE_NAME_PREFIX}_{table_name}"
            wr.s3.to_parquet(
                df=data,
                path=f"{TRANSFORMED_PATH}/{table_name}/",
                dataset=True,
                mode="overwrite_partitions",
                database=DATABASE_NAME_TRANSFORMED,
                table=table,
                partition_cols=partition_cols,
                schema_evolution=False,
            )

        else:
            logger.error(f"No new {table_name} data found.")

        # Check for anomalies in rows of data processed
        # by comparing with previous data processed metrics
        historical_data = get_metrics(
            cloudwatch,
            METRIC_NAMESPACE,
            METRIC_NAME,
            table_name,
            ANOMALY_LOOKBACK_DAYS,
        )

        row_count = len(data)
        detect_anomalies(row_count, historical_data, ANOMALY_STANDARD_DEVIATION)
        publish_metric(cloudwatch, METRIC_NAMESPACE, METRIC_NAME, table_name, row_count)

    logger.info("ETL process completed successfully.")


if __name__ == "__main__":
    job = Job(glueContext)
    job.init(JOB_NAME, args)
    process_data()
    job.commit()
