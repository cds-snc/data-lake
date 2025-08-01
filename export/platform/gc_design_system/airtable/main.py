import json
import boto3
import os
import urllib.request

# Environment variables
AIRTABLE_API_KEY_PARAMETER_NAME = os.environ.get('AIRTABLE_API_KEY_PARAMETER_NAME')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
S3_OBJECT_PREFIX = os.environ.get('S3_OBJECT_PREFIX')

# Airtable configuration (hardcoded like Freshdesk domain)
AIRTABLE_BASE_ID = "appaMppKljeU8zJE1"
AIRTABLE_TABLE_NAME = "tbllQrJwtozOb0Ziv"


def get_airtable_api_key():
    """Retrieve Airtable API key from SSM Parameter Store."""
    try:
        ssm = boto3.client('ssm')  # Create client when needed
        response = ssm.get_parameter(
            Name=AIRTABLE_API_KEY_PARAMETER_NAME,
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        raise Exception(f"Failed to retrieve API key from SSM: {str(e)}")


def fetch_all_records():
    """Fetch all records from Airtable with pagination support."""
    api_key = get_airtable_api_key()
    base_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    
    all_records = []
    offset = None

    while True:
        url = base_url
        if offset:
            url += f"?offset={offset}"

        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {api_key}')
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            records = data.get("records", [])
            all_records.extend(records)
            offset = data.get("offset")
            if not offset:
                break  # no more pages

    return all_records


def handler(event, context):
    try:
        records = fetch_all_records()
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Failed to fetch from Airtable: {str(e)}"
        }

    # Convert records to newline-delimited JSON (JSONL) for Athena
    lines = []
    for record in records:
        flattened = {
            "id": record.get("id"),
            **record.get("fields", {}),
            "createdTime": record.get("createdTime")
        }
        lines.append(json.dumps(flattened))

    # Compose file path
    s3_key = f"{S3_OBJECT_PREFIX}/clients.json"

    try:
        s3 = boto3.client('s3')  # Create client when needed
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body="\n".join(lines).encode("utf-8"),
            ContentType="application/json"
        )
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Failed to upload to S3: {str(e)}"
        }

    return {
        "statusCode": 200,
        "body": f"Saved {len(lines)} records to s3://{S3_BUCKET_NAME}/{s3_key}"
    }
