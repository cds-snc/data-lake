"""
Performs the initial load of the Notify data to the transformed S3 bucket.
This is required as the `notification_history` table is not partitioned by date
and the initial load causes memory errors when reading the entire table.

The expectation is that this script will only be run once and then daily increments
of data will be performed by the process_data.py script.
"""

import json
import logging
import glob
import os
import sys
import time

from typing import List, TypedDict

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

SOURCE_PATH = os.getenv("SOURCE_PATH")
TRANSFORMED_PATH = os.getenv("TRANSFORMED_PATH")

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


def is_type_compatible(series: pd.Series, field_type: str) -> bool:
    """
    Check if a pandas Series is compatible with a given data type.
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
        "numeric": float,
        "float": float,
        "bool": pd.BooleanDtype(),
        "boolean": pd.BooleanDtype(),
        "timestamp": "datetime64[ns]",
    }
    expected_type = postgres_to_pandas.get(field_type)
    if expected_type is None:
        logger.error(f"Unknown Glue type '{field_type}' for validation.")
        return False
    try:
        series.astype(expected_type)
    except (ValueError, TypeError):
        return False
    return True


def load_data(
    table_name: str,
    path: str,
    fields: List[Field],
    partition_timestamp: str = None,
    partition_cols: List[str] = None,
) -> int:
    """
    Reads the data in chunks from local parquet files, validates the schema,
    and saves the transformed data to the target directory.
    """
    try:

        rows = 0
        field_names = [field["name"] for field in fields]
        logger.info(f"Reading {path} data...")

        # Find all parquet files in the directory
        parquet_files = glob.glob(os.path.join(path, "**/*.parquet"), recursive=True)

        for file_path in parquet_files:
            parquet_file = pq.ParquetFile(file_path)

            # Read in chunks
            for batch in parquet_file.iter_batches(
                batch_size=100000, columns=field_names
            ):
                data = pa.Table.from_batches([batch]).to_pandas()
                rows += len(data)

                # Process timestamps
                for field in fields:
                    if field["type"] == "timestamp":
                        date_column = field["name"]
                        data[date_column] = pd.to_datetime(
                            data[date_column],
                            format="%Y-%m-%d %H:%M:%S.%f",
                            errors="coerce",
                        )
                        data[date_column] = data[date_column].dt.tz_localize(None)

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

                # Validate schema
                if not validate_schema(data, fields):
                    raise ValueError(
                        f"Schema validation failed for {table_name}. Aborting ETL process."
                    )

                logger.info(f"Saving {len(data)} records to {table_name}...")

                # Create local dir and save
                output_dir = f"{TRANSFORMED_PATH}/{table_name}/"
                os.makedirs(output_dir, exist_ok=True)
                table_pa = pa.Table.from_pandas(data)
                pq.write_to_dataset(
                    table_pa,
                    root_path=output_dir,
                    partition_cols=partition_cols,
                    existing_data_behavior="overwrite_or_ignore",
                )

        return rows

    except Exception as e:
        logger.error(f"Error processing {path} data: {str(e)}")
        return 0


def get_dataset_config():
    """
    Loads dataset configuration from JSON files in the tables directory.
    Each JSON file contains table metadata along with the fields to load and their type.
    """
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


def initial_load():
    """
    Main ETL process to read and transform local data.
    """

    datasets = get_dataset_config()
    for dataset in datasets:
        start_time = time.time()
        table_name = dataset.get("table_name")
        path = f"{SOURCE_PATH}/public.{table_name}"

        logger.info(f"Loading {table_name} data...")
        rows = load_data(
            table_name,
            path,
            dataset.get("fields"),
            dataset.get("partition_timestamp"),
            dataset.get("partition_cols"),
        )
        processing_time = time.time() - start_time
        logger.info(
            f"Loaded {rows} of data for {table_name} in {processing_time:.2f} seconds"
        )

    logger.info("Initial load completed successfully.")


if __name__ == "__main__":
    initial_load()
