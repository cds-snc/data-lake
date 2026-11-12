import json
import logging
import sys

from datetime import datetime, timezone
from typing import List, Optional
import zipfile

import awswrangler as wr
import boto3
import pandas as pd

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
        "table_name_prefix",
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
TABLE_NAME_PREFIX = args["table_name_prefix"]
GX_CONFIG_OBJECT = args["gx_config_object"]


# Initialize logging
logger = logging.getLogger(__name__)
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
    """
    if "test" in target_gx_bucket:
        logger.info("Not writing validation result to S3 (test bucket)")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    key = f"platform/gc-forms/data-validation/validations/{suite_name}/{timestamp}.json"
    try:
        boto3.client("s3").put_object(
            Bucket=target_gx_bucket,
            Key=key,
            Body=json.dumps(result.to_json_dict(), default=str).encode("utf-8"),
        )
        logger.info(f"Validation result written to s3://{target_gx_bucket}/{key}")
    except Exception as e:
        logger.warning(f"Could not write validation result to S3: {str(e)}")


def log_failed_expectation(res, dataframe: pd.DataFrame) -> None:
    """
    Log the details of a failed expectation, including a sample of the actual
    values in the column.
    """
    expectation_type = res.expectation_config.type
    expectation_definition = res.expectation_config.kwargs
    column = expectation_definition.get("column", "")
    result_details = res.result or {}

    logger.error(
        f"Failed expectation: {expectation_type} on column '{column}'. "
        f"Expectation definition: {expectation_definition}. "
        f"Run details: {result_details}"
    )

    if column and column in dataframe.columns:
        samples = dataframe[column].head(5).astype(str).tolist()
        logger.error(f"Sample values in column '{column}': {samples}")
        logger.error(f"Column dtype: {dataframe[column].dtype}")
    elif column:
        logger.error(f"Column '{column}' is missing from the DataFrame")


def validate_with_gx(dataframe: pd.DataFrame, suite_name: str) -> bool:
    """
    Validate the DataFrame using the specified Great Expectations suite.
    Logs detailed errors if validation fails.
    """
    try:
        suite = load_expectation_suite(suite_name)

        context = gx.get_context(mode="ephemeral")
        data_source = context.data_sources.add_pandas(name="pandas_datasource")
        data_asset = data_source.add_dataframe_asset(name=suite_name)
        batch_definition = data_asset.add_batch_definition_whole_dataframe(
            "runtime_batch"
        )
        suite = context.suites.add(suite)
        validation_definition = context.validation_definitions.add(
            gx.ValidationDefinition(
                name=f"{suite_name}_validation",
                data=batch_definition,
                suite=suite,
            )
        )

        result = validation_definition.run(batch_parameters={"dataframe": dataframe})

        store_validation_result(result, suite_name, SOURCE_BUCKET)

        if not result.success:
            logger.error(f"Validation failed for suite '{suite_name}'")
            for res in result.results:
                if not res.success:
                    log_failed_expectation(res, dataframe)
            return False
        logger.info(f"Validation succeeded for suite '{suite_name}'.")
        return True
    except Exception as e:
        logger.error(f"Error during Great Expectations validation: {str(e)}")
        return False


def get_new_data(
    path: str,
    date_columns: List[str],
    drop_columns: Optional[List[str]],
    email_columns: Optional[List[str]],
    field_count_columns: Optional[List[str]],
    partition_columns: Optional[List[str]],
    partition_timestamp: Optional[str],
) -> pd.DataFrame:
    """
    Reads the data from the specified path in S3 and returns a DataFrame.
    This method is responsible for ensuring the data types are correct.

    To limit unnecessary data processing, the data is filtered to only include
    items that have been modified in the last 24 hours.
    """
    data = pd.DataFrame()
    try:
        yesterday = pd.Timestamp.today(tz="UTC") - pd.Timedelta(days=1)

        logger.info(
            f"Reading s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/{path}/ data from S3 from {yesterday}..."
        )
        data = wr.s3.read_parquet(
            path=f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/{path}/",
            use_threads=True,
            dataset=True,
            last_modified_begin=yesterday,
        )
        data.columns = [col.lower() for col in data.columns]

        # Ensure date columns are parsed correctly and all timezones are treated as UTC
        for date_column in date_columns:
            data[date_column] = pd.to_datetime(data[date_column], errors="coerce")
            data[date_column] = data[date_column].dt.tz_localize(None)

        # Drop unwanted columns
        if drop_columns:
            data = data.drop(columns=drop_columns)

        # Replace email addresses with only the email domain
        if email_columns:
            for column in email_columns:
                data[column] = data[column].str.extract(r"@([^@]+)$", expand=False)

        # If field count columns, make sure they are present and initialized to 0
        # Because of how the Forms ETL works, these columns may not be present in the
        # day's processed data export
        if field_count_columns:
            for column in field_count_columns:
                if column not in data.columns:
                    data[column] = 0

        # Partition the data
        if partition_timestamp and partition_columns:
            partition_format = {
                "month": "%Y-%m",
                "year": "%Y",
            }
            for partition in partition_columns:
                data[partition] = data[partition_timestamp].dt.strftime(
                    partition_format[partition]
                )

    except wr.exceptions.NoFilesFound:
        logger.error(f"No new {path} data found.")
    return data


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


def process_data(datasets: Optional[List[dict]] = None) -> None:
    """
    Main ETL process to read data from S3, validate the schema, and save the
    transformed data back to S3.
    """

    s3 = boto3.client("s3")
    download_s3_object(s3, GX_CONFIG_OBJECT, "gx.zip")

    if datasets is None:
        datasets = [
            {
                "path": "historical-data",
                "date_columns": ["created_at"],
                "partition_timestamp": "created_at",
                "partition_columns": ["year", "month"],
                "email_columns": ["email", "emaildeliveryaddress"],
                "write_mode": "overwrite",
            },
            {
                "path": "processed-data/submissions",
                "date_columns": ["timestamp"],
                "partition_timestamp": "timestamp",
                "gx_suite": "forms-submissions_suite",
            },
            {
                "path": "processed-data/submissions_files",
                "date_columns": ["timestamp"],
                "partition_timestamp": "timestamp",
                "gx_suite": "forms-submissions_files_suite",
            },
            {
                "path": "processed-data/template",
                "date_columns": [
                    "ttl",
                    "api_created_at",
                    "timestamp",
                    "closingdate",
                    "created_at",
                    "updated_at",
                ],
                "field_count_columns": [
                    "checkbox_count",
                    "combobox_count",
                    "dropdown_count",
                    "dynamicrow_count",
                    "fileinput_count",
                    "formatteddate_count",
                    "radio_count",
                    "richtext_count",
                    "starrating_count",
                    "textarea_count",
                    "textfield_count",
                    "addresscomplete_count",
                ],
                "partition_timestamp": "timestamp",
                "partition_columns": ["year", "month"],
                "email_columns": ["deliveryemaildestination"],
                "gx_suite": "forms-template_suite",
            },
            {
                "path": "processed-data/templateToUser",
                "date_columns": ["timestamp"],
                "gx_suite": "forms-templatetouser_suite",
                "partition_timestamp": "timestamp",
            },
            {
                "path": "processed-data/templateVersions",
                "date_columns": [
                    "createdat",
                    "updatedat",
                    "publishedat",
                    "supersededat",
                    "timestamp",
                ],
                "partition_timestamp": "timestamp",
                "partition_columns": ["year", "month"],
                "gx_suite": "forms-templateversions_suite",
            },
            {
                "path": "processed-data/user",
                "date_columns": [
                    "emailverified",
                    "lastlogin",
                    "createdat",
                    "timestamp",
                ],
                "partition_timestamp": "timestamp",
                "partition_columns": ["year", "month"],
                "drop_columns": ["name"],
                "email_columns": ["email"],
                "gx_suite": "forms-user_suite",
            },
        ]
    elif isinstance(datasets, dict):
        datasets = [datasets]

    for dataset in datasets:

        path = dataset.get("path")
        date_columns = dataset.get("date_columns")
        drop_columns = dataset.get("drop_columns")
        email_columns = dataset.get("email_columns")
        field_count_columns = dataset.get("field_count_columns")
        partition_columns = dataset.get("partition_columns")
        partition_timestamp = dataset.get("partition_timestamp")
        gx_suite = dataset.get("gx_suite")
        write_mode = dataset.get("write_mode", "append")
        table_name = path.lower().replace("-", "_")
        if "/" in table_name:
            table_name = path.split("/", 1)[1]

        # Retreive the new data
        logger.info(f"Processing {path} data...")
        try:
            data = get_new_data(
                path=path,
                date_columns=date_columns,
                drop_columns=drop_columns,
                email_columns=email_columns,
                field_count_columns=field_count_columns,
                partition_columns=partition_columns,
                partition_timestamp=partition_timestamp,
            )
        except Exception as e:
            logger.error(f"Failed to process {path}: {e}")
            continue

        if not data.empty:
            if gx_suite:
                if not validate_with_gx(data, gx_suite):
                    raise ValueError(
                        f"Great Expectations validation failed for {path}. Aborting ETL process."
                    )

            # Save the transformed data back to S3
            logger.info(f"Saving new {path} DataFrame to S3...")
            table = f"{TABLE_NAME_PREFIX}_{table_name}"
            wr.s3.to_parquet(
                df=data,
                path=f"{TRANSFORMED_PATH}/{path}/",
                dataset=True,
                mode=write_mode,
                database=DATABASE_NAME_TRANSFORMED,
                table=table,
                partition_cols=partition_columns,
                schema_evolution=True,
            )

        else:
            logger.info(f"No new {path} data found.")

    logger.info("ETL process completed successfully.")


if __name__ == "__main__":
    process_data()
