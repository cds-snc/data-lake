import json
import logging
import sys

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

import awswrangler as wr
import boto3
import pandas as pd
import zipfile

from awsglue.utils import getResolvedOptions

import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
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
GX_SUITE_NAME = "freshdesk_suite"


# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)


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
    Write the Great Expectations validation result to S3. Great Expectations 1.x
    no longer ships an S3 store backend, so the result is written directly.
    A failure to store the result never fails the validation itself.

    The prefix sits outside the crawled raw data path (platform/support/freshdesk)
    so the validation JSON is not picked up by the Freshdesk crawler.
    """
    if "test" in target_gx_bucket:
        logger.info("Not writing validation result to S3 (test bucket)")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    key = f"platform/support/data-validation/freshdesk/validations/{suite_name}/{timestamp}.json"
    try:
        boto3.client("s3").put_object(
            Bucket=target_gx_bucket,
            Key=key,
            Body=json.dumps(result.to_json_dict(), default=str).encode("utf-8"),
        )
        logger.info(f"Validation result written to s3://{target_gx_bucket}/{key}")
    except Exception as e:
        logger.warning(f"Could not write validation result to S3: {str(e)}")


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
    Validate the DataFrame using the Great Expectations suite.
    Logs detailed errors if validation fails.
    """
    try:
        suite = load_expectation_suite(GX_SUITE_NAME)

        context = gx.get_context(mode="ephemeral")
        data_source = context.data_sources.add_pandas(name="pandas_datasource")
        data_asset = data_source.add_dataframe_asset(name="freshdesk_data")
        batch_definition = data_asset.add_batch_definition_whole_dataframe(
            "runtime_batch"
        )
        suite = context.suites.add(suite)
        validation_definition = context.validation_definitions.add(
            gx.ValidationDefinition(
                name=f"{GX_SUITE_NAME}_validation",
                data=batch_definition,
                suite=suite,
            )
        )

        result = validation_definition.run(batch_parameters={"dataframe": dataframe})

        store_validation_result(result, GX_SUITE_NAME, SOURCE_BUCKET)

        if not result.success:
            logger.error(f"Validation failed for suite '{GX_SUITE_NAME}'")
            return False
        logger.info(f"Validation succeeded for suite '{GX_SUITE_NAME}'.")
        return True
    except Exception as e:
        logger.error(f"Error during Great Expectations validation: {str(e)}")
        return False


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
