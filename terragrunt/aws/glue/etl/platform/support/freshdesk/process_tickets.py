import logging
import sys

from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta

import awswrangler as wr
import boto3
import numpy as np
import pandas as pd

from awsglue.utils import getResolvedOptions

args = getResolvedOptions(
    sys.argv,
    [
        "source_bucket",
        "source_prefix",
        "transformed_bucket",
        "transformed_prefix",
        "database_name_raw",
        "database_name_transformed",
        "table_name",
    ],
)

SOURCE_BUCKET = args["source_bucket"]
SOURCE_PREFIX = args["source_prefix"]
TRANSFORMED_BUCKET = args["transformed_bucket"]
TRANSFORMED_PREFIX = args["transformed_prefix"]
TRANSFORMED_PATH = f"s3://{TRANSFORMED_BUCKET}/{TRANSFORMED_PREFIX}"
PARTITION_KEY = "month"
DATABASE_NAME_RAW = args["database_name_raw"]
DATABASE_NAME_TRANSFORMED = args["database_name_transformed"]
TABLE_NAME = args["table_name"]

# Anomaly detection configuration
METRIC_NAMESPACE = "data-lake/etl/freshdesk"
METRIC_NAME = "ProcessedRecordCount"
ANOMALY_LOOKBACK_DAYS = 14
ANOMALY_STANDARD_DEVIATION = 3.0

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)


def validate_schema(dataframe: pd.DataFrame, glue_table_schema: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame conforms to the Glue table schema.
    """
    for _, row in glue_table_schema.iterrows():
        column_name = row["Column Name"]
        column_type = row["Type"]
        if column_name not in dataframe.columns:
            logger.error(f"Validation failed: Missing column '{column_name}'")
            return False

        if not is_type_compatible(dataframe[column_name], column_type):
            logger.error(
                f"Validation failed: Column '{column_name}' type mismatch. Expected {column_type}"
            )
            return False
    return True


def is_type_compatible(series: pd.Series, glue_type: str) -> bool:
    """
    Check if a pandas Series is compatible with a Glue type.
    """
    glue_to_pandas = {
        "string": pd.StringDtype(),
        "int": pd.Int64Dtype(),
        "bigint": pd.Int64Dtype(),
        "double": float,
        "float": float,
        "boolean": bool,
        "date": "datetime64[ns]",
        "timestamp": "datetime64[ns]",
        "array<string>": pd.StringDtype(),
    }
    expected_type = glue_to_pandas.get(glue_type.lower())
    if expected_type is None:
        logger.error(f"Unknown Glue type '{glue_type}' for validation.")
        return False
    try:
        series.astype(expected_type)
    except (ValueError, TypeError):
        return False
    return True


def get_days_tickets(day: datetime) -> pd.DataFrame:
    """
    Load the JSON file containing the tickets for a specific day.
    """
    day_formatted = day.strftime("%Y-%m-%d")
    source_file_path = f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}{PARTITION_KEY}={day_formatted[:7]}/{day_formatted}.json"
    logger.info(f"Loading source JSON file: {source_file_path}")
    new_tickets = pd.DataFrame()
    try:
        new_tickets = wr.s3.read_json(source_file_path, dtype=True)

        # Ensure date columns are parsed correctly and all timezones are treated as UTC
        for date_column in ["created_at", "updated_at", "due_by", "fr_due_by"]:
            new_tickets[date_column] = pd.to_datetime(
                new_tickets[date_column], errors="coerce"
            )
            new_tickets[date_column] = new_tickets[date_column].dt.tz_localize(None)

    except wr.exceptions.NoFilesFound:
        logger.warning("No new tickets found.")
    return new_tickets


def get_existing_tickets(start_date: str) -> pd.DataFrame:
    """
    Load the existing transformed data from the S3 bucket.
    """
    start_date_formatted = start_date.strftime("%Y-%m")
    logger.info(f"Loading transformed data from {start_date_formatted} onwards...")
    existing_tickets = pd.DataFrame()
    try:
        existing_tickets = wr.s3.read_parquet(
            path=TRANSFORMED_PATH,
            dataset=True,
            partition_filter=(
                lambda partition: partition[PARTITION_KEY] >= start_date_formatted
            ),
        )
        existing_tickets["updated_at"] = existing_tickets["updated_at"].dt.tz_localize(
            None
        )  # Treat all as UTC
    except wr.exceptions.NoFilesFound:
        logger.warning("No existing data found. Starting fresh.")

    return existing_tickets


def merge_tickets(
    existing_tickets: pd.DataFrame, new_tickets: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge the existing and new tickets DataFrames.
    """
    if existing_tickets.empty:
        return new_tickets

    existing_tickets["id"] = existing_tickets["id"].astype(str)
    new_tickets["id"] = new_tickets["id"].astype(str)

    combined_tickets = pd.concat([existing_tickets, new_tickets], ignore_index=True)
    combined_tickets = combined_tickets.sort_values(
        by=["id", "updated_at"], ascending=[True, False]
    )
    combined_tickets = combined_tickets.drop_duplicates(subset=["id"], keep="first")

    return combined_tickets


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
    timestamp = datetime.now(timezone.utc)
    cloudwatch.put_metric_data(
        Namespace=metric_namespace,
        MetricData=[
            {
                "MetricName": metric_name,
                "Dimensions": [{"Name": "Dataset", "Value": dataset_name}],
                "Value": metric_value,
                "Timestamp": timestamp,
                "Unit": "Count",
            },
        ],
    )
    logger.info(f"Published metrics for {dataset_name}: {metric_value} records")


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

        # There is strong seasonality in the data, so we remove any 0 values,
        # as they indicate no data was recorded
        metrics = metrics[metrics > 0]

        logger.info(f"Retrieved {metrics} metrics for {dataset_name} from CloudWatch.")
        return metrics

    except Exception as e:
        logger.error(f"Error fetching CloudWatch metric data: {e}")
        return None


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
            f"Anomaly: Latest value {row_count}, mean: {mean:.2f}, "
            f"stdev: {standard_deviation:.2f}, z_score: {z_score:.2f}"
        )
    return is_anomaly


def process_tickets():
    """
    Load the new tickets, validate the schema, and merge with existing data.
    """
    cloudwatch = boto3.client("cloudwatch")

    # Get yesterday's tickets
    yesterday = datetime.now(timezone.utc) - relativedelta(days=1)
    new_tickets = get_days_tickets(yesterday)

    if not new_tickets.empty:

        # Check that the new tickets schema matches the expected schema
        glue_table_schema = wr.catalog.table(
            database=DATABASE_NAME_RAW, table=TABLE_NAME
        )
        if not validate_schema(new_tickets, glue_table_schema):
            raise ValueError("Schema validation failed. Aborting ETL process.")

        # Load 1 year of existing ticket data
        start_date = datetime.now(timezone.utc) - relativedelta(years=1)
        existing_tickets = get_existing_tickets(start_date)

        # Merge the existing and new tickets and save
        combined_tickets = merge_tickets(existing_tickets, new_tickets)

        logger.info("Saving updated DataFrame to S3...")
        wr.s3.to_parquet(
            df=combined_tickets,
            path=TRANSFORMED_PATH,
            dataset=True,
            mode="overwrite_partitions",
            database=DATABASE_NAME_TRANSFORMED,
            table=TABLE_NAME,
            partition_cols=[PARTITION_KEY],
        )
        logger.info("ETL process completed successfully.")
    else:
        logger.info("No new tickets found. Aborting ETL process.")

    # Check for anomalies in rows of data processed
    # by comparing with previous data processed metrics
    historical_data = get_metrics(
        cloudwatch,
        METRIC_NAMESPACE,
        METRIC_NAME,
        "new_tickets",
        ANOMALY_LOOKBACK_DAYS,
    )

    new_ticket_count = len(new_tickets)
    detect_anomalies(new_ticket_count, historical_data, ANOMALY_STANDARD_DEVIATION)
    publish_metric(
        cloudwatch, METRIC_NAMESPACE, METRIC_NAME, "new_tickets", new_ticket_count
    )


if __name__ == "__main__":
    process_tickets()
