import logging
import sys

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

import awswrangler as wr
import boto3
import numpy as np
import pandas as pd
import zipfile

from awsglue.utils import getResolvedOptions

import great_expectations as gx
import os

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
        "gx_config_object",
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
GX_CONFIG_OBJECT = args["gx_config_object"]
GX_CHECKPOINT_NAME = "freshdesk_checkpoint"


# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)


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
                    "prefix": "platform/gc-forms/data-validation/validations/",
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


def download_s3_object(s3: boto3.client, s3_url: str, filename: str) -> None:
    """
    Download an S3 object to a local file.
    """
    bucket_name = s3_url.split("/")[2]
    object_key = "/".join(s3_url.split("/")[3:])
    current_dir = os.getcwd()
    s3.download_file(
        Bucket=bucket_name,
        Key=object_key,
        Filename=os.path.join(current_dir, filename),
    )

    gx_zip = os.path.join(current_dir, os.path.basename(filename))
    gx_dir = os.path.join(current_dir, os.path.splitext(gx_zip)[0])

    with zipfile.ZipFile(gx_zip, "r") as zip_ref:
        zip_ref.extractall(gx_dir)


def validate_with_gx(dataframe: pd.DataFrame) -> bool:
    """
    Validate the DataFrame using the specified Great Expectations checkpoint.
    Logs detailed errors if validation fails.
    """
    gx_context_path = os.path.join(os.getcwd(), "gx")
    context = gx.get_context(context_root_dir=gx_context_path, cloud_mode=False)

    configure_gx_stores(context, SOURCE_BUCKET)

    result = context.run_checkpoint(
        checkpoint_name=GX_CHECKPOINT_NAME,
        batch_request={
            "runtime_parameters": {"batch_data": dataframe},
            "batch_identifiers": {"default_identifier_name": "runtime_batch"},
        },
    )
    if not result["success"]:
        logger.error(f"Validation failed for checkpoint '{GX_CHECKPOINT_NAME}'")
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
    logger.info(f"Validation succeeded for checkpoint '{GX_CHECKPOINT_NAME}'.")
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
        logger.warn("No new tickets found.")
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
        logger.warn("No existing data found. Starting fresh.")

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


def process_tickets():
    """
    Load the new tickets, validate the schema, and merge with existing data.
    """
    s3 = boto3.client("s3")
    download_s3_object(s3, GX_CONFIG_OBJECT, "gx.zip")

    # Get yesterday's tickets
    yesterday = datetime.now(timezone.utc) - relativedelta(days=1)
    new_tickets = get_days_tickets(yesterday)

    if not new_tickets.empty:

        if not validate_with_gx(new_tickets):
            raise ValueError(
                "Great Expectations validation failed. Aborting ETL process."
            )

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



if __name__ == "__main__":
    process_tickets()
