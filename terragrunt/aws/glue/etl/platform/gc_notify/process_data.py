import json
import logging
import os
import sys
import time
import zipfile

from datetime import datetime, timezone
from typing import List, TypedDict

import awswrangler as wr
import boto3
import pandas as pd
import pyarrow.dataset as ds

from awsglue.utils import getResolvedOptions

args = getResolvedOptions(
    sys.argv,
    [
        "source_bucket",
        "source_prefix",
        "transformed_bucket",
        "transformed_prefix",
        "database_name_transformed",
        "table_config_object",
        "table_name_prefix",
    ],
)

# Data source and target
SOURCE_BUCKET = args["source_bucket"]
SOURCE_PREFIX = args["source_prefix"]
TRANSFORMED_BUCKET = args["transformed_bucket"]
TRANSFORMED_PREFIX = args["transformed_prefix"]
TRANSFORMED_PATH = f"s3://{TRANSFORMED_BUCKET}/{TRANSFORMED_PREFIX}"
DATABASE_NAME_TRANSFORMED = args["database_name_transformed"]
TABLE_CONFIG_OBJECT = args["table_config_object"]
TABLE_NAME_PREFIX = args["table_name_prefix"]

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)


class Field(TypedDict):
    name: str
    type: str


def validate_schema(
    dataframe: pd.DataFrame,
    fields: List[Field],
) -> bool:
    """
    Validate that the DataFrame conforms to the expected table schema.
    """
    for field in fields:
        field_name = field["name"]
        field_type = field["type"]
        if field_name not in dataframe.columns:
            logger.error(f"Validation failed: Missing column '{field_name}'")
            return False

        if not is_type_compatible(dataframe[field_name], field_type):
            logger.error(
                f"Validation failed: Column '{field_name}' type mismatch. Expected {field_type} but got {dataframe[field_name].dtype}"
            )
            return False

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


def is_type_compatible(series: pd.Series, field_type: str) -> bool:
    """
    Check if a pandas Series is compatible with a given data type.
    """
    expected_type = postgres_to_pandas_type(field_type)
    if expected_type is None:
        logger.error(f"Unknown Postgres type '{field_type}' for validation.")
        return False
    try:
        series.astype(expected_type)
    except (ValueError, TypeError):
        return False
    return True


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


def publish_metric(cloudwatch, dataset_name, count, processing_time):
    """
    Publish data processing metrics to CloudWatch
    """
    timestamp = datetime.now(timezone.utc)
    cloudwatch.put_metric_data(
        Namespace="data-lake/etl/gc-notify",
        MetricData=[
            {
                "MetricName": "ProcessedRecordCount",
                "Dimensions": [{"Name": "Dataset", "Value": dataset_name}],
                "Value": count,
                "Timestamp": timestamp,
                "Unit": "Count",
            },
            {
                "MetricName": "ProcessingTime",
                "Dimensions": [{"Name": "Dataset", "Value": dataset_name}],
                "Value": processing_time,
                "Timestamp": timestamp,
                "Unit": "Seconds",
            },
        ],
    )
    logger.info(
        f"Published metrics for {dataset_name}: {count} records in {processing_time:.2f}s"
    )


def get_dataset_config():
    datasets = []

    current_dir = os.getcwd()
    tables_dir = os.path.join(current_dir, "tables")
    tables_zip = os.path.join(current_dir, "tables.zip")

    with zipfile.ZipFile(tables_zip, "r") as zip_ref:
        zip_ref.extractall(tables_dir)

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


def download_s3_object(s3, s3_url, filename):
    """
    Download an S3 object to a local file.
    """
    bucket_name = s3_url.split("/")[2]
    object_key = "/".join(s3_url.split("/")[3:])
    s3.download_file(
        Bucket=bucket_name,
        Key=object_key,
        Filename=os.path.join(os.getcwd(), filename),
    )


def get_incremental_load_date_from(data_retention_days: int) -> str:
    """
    Get the date from which to load incremental data.  This will always be the beginning of
    the month that is today minus the retention days.  The reason for this is because we
    perform a month partition overwrite and need to make sure that we are loading
    all data within the overwritten month partition(s) while respecting the data retention policy.
    """
    today = pd.Timestamp.now().normalize()
    month_start = (today - pd.DateOffset(days=data_retention_days)).replace(day=1)
    return month_start.strftime("%Y-%m-%d %H:%M:%S")


def process_data():
    """
    Main ETL process to read data from S3, validate the schema, and save the
    transformed data back to S3.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    path_prefix = f"notification-canada-ca-staging-cluster-{today}/NotificationCanadaCastaging/public."
    cloudwatch = boto3.client("cloudwatch")
    s3 = boto3.client("s3")

    # Download the table configuration file from S3
    download_s3_object(s3, TABLE_CONFIG_OBJECT, "tables.zip")

    # Read the dataset configuration and start processing
    datasets = get_dataset_config()
    for dataset in datasets:
        start_time = time.time()
        table_name = dataset.get("table_name")
        path = f"{path_prefix}{table_name}"
        partition_cols = dataset.get("partition_cols")
        incremental_load = dataset.get("incremental_load", False)
        retention_days = dataset.get("retention_days", 0)

        # Retrieve the new data
        logger.info(f"Processing {table_name} data...")
        data = get_new_data(
            path,
            dataset.get("fields"),
            dataset.get("partition_timestamp"),
            partition_cols,
            date_from=(
                get_incremental_load_date_from(retention_days)
                if incremental_load
                else None
            ),
        )
        if not data.empty:
            if not validate_schema(data, dataset.get("fields")):
                raise ValueError(
                    f"Schema validation failed for {table_name}. Aborting ETL process."
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

        # Publish metrics to CloudWatch
        processing_time = time.time() - start_time
        publish_metric(cloudwatch, path, len(data), processing_time)

    logger.info("ETL process completed successfully.")


if __name__ == "__main__":
    process_data()
