import logging
import sys

from typing import List

import awswrangler as wr
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
        "table_name_prefix",
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

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)


def validate_schema(
    dataframe: pd.DataFrame,
    non_source_columns: List[str],
    glue_table_schema: pd.DataFrame,
) -> bool:
    """
    Validate that the DataFrame conforms to the Glue table schema.  The `non_source_columns`
    specifies extra columns that are allowed to be in the DataFrame but are not part of
    the Glue schema.
    """
    for _, row in glue_table_schema.iterrows():
        column_name = row["Column Name"]
        column_type = row["Type"]
        if column_name not in dataframe.columns:
            logger.error(f"Validation failed: Missing column '{column_name}'")
            return False

        if not is_type_compatible(dataframe[column_name], column_type):
            logger.error(
                f"Validation failed: Column '{column_name}' type mismatch. Expected {column_type} but got {dataframe[column_name].dtype}"
            )
            return False

    for column_name in dataframe.columns:
        if column_name not in glue_table_schema["Column Name"].values:
            if non_source_columns and column_name not in non_source_columns:
                logger.error(f"Validation failed: Extra column '{column_name}'")
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
        "boolean": pd.BooleanDtype(),
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


def get_new_data(
    path: str,
    date_columns: List[str],
    sort_columns: List[str],
    partition_created_column: str = None,
) -> pd.DataFrame:
    """
    Reads the data from the specified path in S3 and returns a DataFrame.
    This method is responsible for ensuring the data types are correct and
    that only the most recent duplicate items are kept.

    To limit unnecessary data processing, the data is filtered to only include
    items that have been modified in the last 24 hours.
    """
    data = pd.DataFrame()
    try:
        logger.info(
            f"Reading s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/{path}/ data from S3..."
        )
        yesterday = pd.Timestamp.today(tz="UTC") - pd.Timedelta(days=1)
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

        # Sort data by specified columns ascending, except for the timestamp column
        # which we sort descending.  This groups all duplicate items and allows us
        # to keep only the most recent duplicate.
        if sort_columns:
            data = data.sort_values(
                by=sort_columns + ["timestamp"],
                ascending=[True] * len(sort_columns) + [False],
            )
            data = data.drop_duplicates(subset=sort_columns, keep="first")

        if partition_created_column:
            data["month"] = data[partition_created_column].dt.strftime("%Y-%m")

    except wr.exceptions.NoFilesFound:
        logger.error(f"No new {path} data found.")
    return data


def remove_old_data(path: str, table: str, partition_cols: List[str]):
    """
    Remove transformed data that was not exported today
    """
    data = wr.s3.read_parquet(
        path=f"s3://{TRANSFORMED_BUCKET}/{TRANSFORMED_PREFIX}/{path}/",
        use_threads=True,
        dataset=True,
    )
    yesterday = pd.Timestamp.today() - pd.Timedelta(days=1)
    data = data[data["timestamp"] > yesterday]

    # Check if there is any data left to save.  This is a safety mechanism to avoid
    # removing all data if the Forms data sync fails.
    if data.empty:
        logger.error(f"No new {path} data found after pruning.")
    else:
        wr.s3.to_parquet(
            df=data,
            path=f"{TRANSFORMED_PATH}/{path}/",
            dataset=True,
            mode="overwrite_partitions",
            database=DATABASE_NAME_TRANSFORMED,
            table=table,
            partition_cols=partition_cols,
        )


def process_data():
    """
    Main ETL process to read data from S3, validate the schema, and save the
    transformed data back to S3.
    """
    datasets = [
        {
            "path": "historical-data",
            "date_columns": ["date"],
            "sort_columns": None,
            "partition_created_column": "date",
            "partition_columns": ["month"],
            "prune_old_data": False,
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
            "sort_columns": ["id"],
            "partition_created_column": "created_at",
            "partition_columns": ["month"],
            "prune_old_data": True,
        },
        {
            "path": "processed-data/templateToUser",
            "date_columns": ["timestamp"],
            "sort_columns": ["templateid", "userid"],
            "partition_created_column": None,
            "partition_columns": None,
            "prune_old_data": True,
        },
        {
            "path": "processed-data/user",
            "date_columns": ["emailverified", "lastlogin", "createdat", "timestamp"],
            "sort_columns": ["id"],
            "partition_created_column": "lastlogin",  # User created date is currently in this field
            "partition_columns": ["month"],
            "prune_old_data": True,
        },
    ]

    for dataset in datasets:
        path = dataset.get("path")
        table_name = path.lower().replace("-", "_")
        if "/" in table_name:
            table_name = path.split("/", 1)[1]

        # Retreive the new data
        logger.info(f"Processing {path} data...")
        data = get_new_data(
            path,
            dataset.get("date_columns"),
            dataset.get("sort_columns"),
            dataset.get("partition_created_column"),
        )
        if data.empty:
            logger.info(f"No new {path} data found.")
            continue

        # Validate the data schema
        glue_table_schema = wr.catalog.table(
            database=DATABASE_NAME_RAW, table=f"{TABLE_NAME_PREFIX}_raw_{table_name}"
        )

        if not validate_schema(
            data, dataset.get("partition_columns"), glue_table_schema
        ):
            raise ValueError(
                f"Schema validation failed for {path}. Aborting ETL process."
            )

        # Save the transformed data back to S3
        logger.info(f"Saving new {path} DataFrame to S3...")
        table = f"{TABLE_NAME_PREFIX}_{table_name}"
        partition_cols = dataset.get("partition_columns")
        wr.s3.to_parquet(
            df=data,
            path=f"{TRANSFORMED_PATH}/{path}/",
            dataset=True,
            mode="overwrite_partitions",
            database=DATABASE_NAME_TRANSFORMED,
            table=table,
            partition_cols=partition_cols,
        )

        # Remove transformed data that does not have a `timestamp` from today
        # TODO: Better way to do this that does not involve reading all Transformed data
        if dataset.get("prune_old_data"):
            logger.info(f"Removing old {path} data...")
            remove_old_data(path, table, partition_cols)

    logger.info("ETL process completed successfully.")


# TODO: convert to Glue ETL job with job bookmarks
if __name__ == "__main__":
    process_data()
