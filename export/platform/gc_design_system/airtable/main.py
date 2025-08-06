import json
import boto3
import os
import requests
from time import sleep
from datetime import datetime
import hashlib

# Environment variables
AIRTABLE_API_KEY_PARAMETER_NAME = os.environ.get("AIRTABLE_API_KEY_PARAMETER_NAME")
S3_BUCKET_NAME_TRANSFORMED = os.environ.get("S3_BUCKET_NAME_TRANSFORMED")
S3_BUCKET_NAME_RAW = os.environ.get("S3_BUCKET_NAME_RAW")
S3_OBJECT_PREFIX = os.environ.get("S3_OBJECT_PREFIX")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.environ.get("AIRTABLE_TABLE_NAME")
GLUE_CRAWLER_NAME = os.environ.get("GLUE_CRAWLER_NAME")


def get_airtable_api_key():
    """Retrieve Airtable API key from SSM Parameter Store."""
    try:
        ssm = boto3.client("ssm")  # Create client when needed
        response = ssm.get_parameter(
            Name=AIRTABLE_API_KEY_PARAMETER_NAME, WithDecryption=True
        )
        return response["Parameter"]["Value"]
    except Exception as e:
        raise Exception(f"Failed to retrieve API key from SSM: {str(e)}")


def fetch_all_records():
    """Fetch all records from Airtable with pagination support."""
    api_key = get_airtable_api_key()
    base_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    all_records = []
    offset = None

    headers = {"Authorization": f"Bearer {api_key}"}

    while True:
        params = {}
        if offset:
            params["offset"] = offset

        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        records = data.get("records", [])
        all_records.extend(records)
        offset = data.get("offset")
        if not offset:
            break  # no more pages
        sleep(5)

    return all_records


def handler(event, context):
    try:
        records = fetch_all_records()
    except Exception as e:
        return {"statusCode": 500, "body": f"Failed to fetch from Airtable: {str(e)}"}

    # Convert records to newline-delimited JSON (JSONL) for Athena
    lines = []
    for record in records:
        # Flatten and normalize field names in one step
        flattened = {"id": record.get("id"), "created_time": record.get("createdTime")}
        for key, value in record.get("fields", {}).items():
            normalized_key = (
                key.replace(" ", "_")
                .replace('"', "")
                .replace("(", "")
                .replace(")", "")
                .lower()
            )

            # Strip PII - We are hashing sensitive fields. Some of the fields are already hashed in Airtable, this is just an extra precaution        
            if normalized_key in [
                "name",
                "primary_contact_on_team",
                "main_contact_on_meetings",
                "main_contact_on_engagement",
                "email"
            ]:
                if isinstance(value, list):
                    value = [hashlib.sha256(item.encode("utf-8")).hexdigest() for item in value if isinstance(item, str)]
                elif isinstance(value, str):
                    value = hashlib.sha256(value.encode("utf-8")).hexdigest()

            flattened[normalized_key] = value
        lines.append(json.dumps(flattened))

    date_suffix = datetime.utcnow().strftime("%Y-%m-%d")
    s3_key_transformed = f"{S3_OBJECT_PREFIX}/clients.json"
    s3_key_raw = f"{S3_OBJECT_PREFIX}/clients_{date_suffix}.json"

    try:
        s3 = boto3.client("s3")  # Create client when needed
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
        "body": f"Saved {len(lines)} records to s3://{S3_BUCKET_NAME_TRANSFORMED}/{s3_key_raw} and s3://{S3_BUCKET_NAME_TRANSFORMED}/{s3_key_transformed}",
    }
