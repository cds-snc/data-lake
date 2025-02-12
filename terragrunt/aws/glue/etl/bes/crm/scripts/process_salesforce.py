import sys

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
        "database_name_transformed",
        "table_name",
    ],
)

SOURCE_BUCKET = args["source_bucket"]
SOURCE_PREFIX = args["source_prefix"]
TRANSFORMED_BUCKET = args["transformed_bucket"]
TRANSFORMED_PREFIX = args["transformed_prefix"]
DATABASE_NAME_TRANSFORMED = args["database_name_transformed"]
TABLE_NAME = args["table_name"]

# S3 Paths
source_path = f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}"
destination_path = f"s3://{TRANSFORMED_BUCKET}/{TRANSFORMED_PREFIX}"

# AWS Glue Database & Table Name
glue_database = DATABASE_NAME_TRANSFORMED
glue_table = TABLE_NAME

# Read Account and Opportunity tables separately
account_df = wr.s3.read_csv(path=source_path + "Account.csv")
opportunity_df = wr.s3.read_csv(path=source_path + "Opportunity.csv")

# Drop nulls to avoid join issues
account_df.dropna(subset=["Id"], inplace=True)
opportunity_df.dropna(subset=["AccountId"], inplace=True)

# Convert IDs to string to avoid mismatches
account_df["Id"] = account_df["Id"].astype(str)
opportunity_df["AccountId"] = opportunity_df["AccountId"].astype(str)

# Perform Inner Join
df_transformed = account_df.merge(
    opportunity_df, left_on="Id", right_on="AccountId", how="inner"
)

# Rename conflicting columns
df_transformed = df_transformed.rename(columns={"Name_x": "AccountName", "CreatedDate_x": "AccountCreatedDate",
                                       "CreatedDate_y": "OpportunityCreatedDate", "Id_y": "OpportunityId", "Name_y": "OpportunityName"})

# Select only required columns
df_transformed = df_transformed[["AccountId", "AccountName", "AccountCreatedDate",
                                 "OpportunityId", "OpportunityName", "OpportunityCreatedDate", "Product_to_Add__c"]]

# Ensure date columns are parsed correctly and all timezones are treated as UTC
for date_column in ["AccountCreatedDate", "OpportunityCreatedDate"]:
            df_transformed[date_column] = pd.to_datetime(
                df_transformed[date_column], errors="coerce"
            )
            df_transformed[date_column] = df_transformed[date_column].dt.tz_localize(None)

# Write to S3 in Parquet format
wr.s3.to_parquet(
    df=df_transformed,
    path=destination_path,
    dataset=True,
    database=glue_database,  # Registers table in Glue
    table=glue_table,
    mode="overwrite"  # Replace existing table
)

print(
    f"Data successfully written to {destination_path} and registered in Glue table {glue_table}.")

# Purge the source S3 prefix
wr.s3.delete_objects(path=source_path)

print(f"Source data at {source_path} has been deleted.")