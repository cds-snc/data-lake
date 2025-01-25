import sys

from datetime import datetime, UTC
from dateutil.relativedelta import relativedelta

import awswrangler as wr
import pandas as pd


SOURCE_BUCKET = "cds-data-lake-raw-production"
SOURCE_PREFIX = "platform/support/freshdesk/"
TRANSFORMED_BUCKET = "cds-data-lake-transformed-production"
TRANSFORMED_PREFIX = "platform/support/freshdesk/"
TRANSFORMED_PATH = f"s3://{TRANSFORMED_BUCKET}/{TRANSFORMED_PREFIX}"
PARTITION_KEY = "month"
DATABASE_NAME_RAW = "platform_support_production_raw"
DATABASE_NAME_TRANSFORMED = "platform_support_production"
TABLE_NAME = "platform_support_freshdesk"


def get_existing_tickets(start_date: str) -> pd.DataFrame:
    """
    Load the existing transformed data from the S3 bucket.
    """
    start_date_formatted = start_date.strftime("%Y-%m")
    end_date_formatted = (start_date + relativedelta(months=1)).strftime("%Y-%m")
    print(f"Loading transformed data from {start_date_formatted}")
    existing_tickets = pd.DataFrame()
    try:
        existing_tickets = wr.s3.read_parquet(
            path=TRANSFORMED_PATH,
            dataset=True,
            partition_filter=(
                lambda partition: partition[PARTITION_KEY] >= start_date_formatted and partition[PARTITION_KEY] < end_date_formatted
            ),
        )
        existing_tickets["updated_at"] = existing_tickets["updated_at"].dt.tz_localize(
            None
        )  # Treat all as UTC
    except wr.exceptions.NoFilesFound:
        print("No existing data found. Starting fresh.")

    return existing_tickets


def process_tickets(date: datetime):
    tickets = get_existing_tickets(date)

    print(f"Loaded {len(tickets)} existing tickets.")

    # Remove tickets with a type column that equals 'Performing tests'
    tickets = tickets[tickets["type"] != "Performing tests"]

    print(f"Saving {len(tickets)} filtered tickets.")

    print("Saving updated DataFrame to S3...")
    wr.s3.to_parquet(
        df=tickets,
        path=TRANSFORMED_PATH,
        dataset=True,
        mode="overwrite_partitions",
        database=DATABASE_NAME_TRANSFORMED,
        table=TABLE_NAME,
        partition_cols=[PARTITION_KEY],
    )
    print("ETL process completed successfully.")


if __name__ == "__main__":
    date = datetime(2022, 12, 10)
    print("============================================")
    print(f"Processing tickets for {date.strftime('%Y-%m')}")
    print("============================================")
    process_tickets(date)
