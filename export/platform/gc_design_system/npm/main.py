import json
import boto3
import os
import requests
from datetime import datetime

# Environment variables
S3_BUCKET_NAME_TRANSFORMED = os.environ.get("S3_BUCKET_NAME_TRANSFORMED")
S3_BUCKET_NAME_RAW = os.environ.get("S3_BUCKET_NAME_RAW")
S3_OBJECT_PREFIX = os.environ.get("S3_OBJECT_PREFIX")
GLUE_CRAWLER_NAME = os.environ.get("GLUE_CRAWLER_NAME")

# NPM package configuration
NPM_PACKAGE = "@cdssnc/gcds-components-vue"
START_YEAR = 2024  # Package start year


def fetch_npm_downloads_for_year(year):
    """Fetch NPM download statistics for a specific year."""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    # Adjust end date for current year to avoid future dates
    current_year = datetime.now().year
    if year == current_year:
        end_date = datetime.now().strftime("%Y-%m-%d")

    url = f"https://api.npmjs.org/downloads/range/{start_date}:{end_date}/{NPM_PACKAGE}"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def fetch_all_npm_data():
    """Fetch NPM download data for all years from package start to current year."""
    current_year = datetime.now().year
    all_data = []

    for year in range(START_YEAR, current_year + 1):
        try:
            year_data = fetch_npm_downloads_for_year(year)

            # Add metadata to each download record
            for download in year_data.get("downloads", []):
                download["package"] = year_data.get("package", NPM_PACKAGE)
                download["year"] = year
                download["fetched_at"] = datetime.utcnow().isoformat()
                all_data.append(download)

        except Exception as e:
            print(f"Warning: Failed to fetch data for year {year}: {str(e)}")
            continue

    return all_data


def handler(event, context):
    try:
        records = fetch_all_npm_data()
    except Exception as e:
        return {"statusCode": 500, "body": f"Failed to fetch from NPM API: {str(e)}"}

    if not records:
        return {"statusCode": 200, "body": "No NPM download data found"}

    # Convert records to newline-delimited JSON (JSONL) for Athena
    lines = [json.dumps(record) for record in records]

    date_suffix = datetime.utcnow().strftime("%Y-%m-%d")
    s3_key_transformed = f"{S3_OBJECT_PREFIX}/npm_downloads.json"
    s3_key_raw = f"{S3_OBJECT_PREFIX}/npm_downloads_{date_suffix}.json"

    try:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=S3_BUCKET_NAME_TRANSFORMED,
            Key=s3_key_transformed,
            Body="\n".join(lines).encode("utf-8"),
            ContentType="application/json",
        )

        s3.put_object(
            Bucket=S3_BUCKET_NAME_RAW,
            Key=s3_key_raw,
            Body="\n".join(lines).encode("utf-8"),
            ContentType="application/json",
        )

        # Trigger Glue crawler to update table schema
        try:
            glue = boto3.client("glue")
            glue.start_crawler(Name=GLUE_CRAWLER_NAME)
        except Exception as crawler_error:
            # Don't fail the whole job if crawler fails
            print(f"Warning: Failed to start crawler: {crawler_error}")

    except Exception as e:
        return {"statusCode": 500, "body": f"Failed to upload to S3: {str(e)}"}

    return {
        "statusCode": 200,
        "body": f"Saved {len(lines)} NPM download records to s3://{S3_BUCKET_NAME_TRANSFORMED}/{s3_key_raw} and s3://{S3_BUCKET_NAME_TRANSFORMED}/{s3_key_transformed}",
    }
