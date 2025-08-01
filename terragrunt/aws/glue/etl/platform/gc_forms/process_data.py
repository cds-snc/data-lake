import logging
import sys

from typing import List, Optional
import zipfile

import awswrangler as wr
import boto3
import pandas as pd

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
                "gx_checkpoint": "forms-submissions_checkpoint",
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
                    "textarea_count",
                    "textfield_count",
                    "addresscomplete_count",
                ],
                "partition_timestamp": "timestamp",
                "partition_columns": ["year", "month"],
                "email_columns": ["deliveryemaildestination"],
                "gx_checkpoint": "forms-template_checkpoint",
            },
            {
                "path": "processed-data/templateToUser",
                "date_columns": ["timestamp"],
                "gx_checkpoint": "forms-templatetouser_checkpoint",
                "partition_timestamp": "timestamp",
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
                "gx_checkpoint": "forms-user_checkpoint",
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
        gx_checkpoint = dataset.get("gx_checkpoint")
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
            if gx_checkpoint:
                if not validate_with_gx(data, gx_checkpoint):
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
