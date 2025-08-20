import json
import boto3
import gzip
import logging
import os
from datetime import datetime
import urllib.parse
from io import BytesIO
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger()
logger.setLevel("INFO")

# Environment variables
S3_BUCKET_NAME_TRANSFORMED = os.environ.get("S3_BUCKET_NAME_TRANSFORMED")
S3_OBJECT_PREFIX = os.environ.get("S3_OBJECT_PREFIX")


def load_cloudfront_log(s3_client, bucket, key):
    """Load a CloudFront .gz log file from S3."""
    logger.info(f"Loading CloudFront log file: s3://{bucket}/{key}")
    
    # Download the file from S3
    response = s3_client.get_object(Bucket=bucket, Key=key)
    
    # Read the gzipped content
    with gzip.open(response['Body'], 'rt') as f:
        lines = f.readlines()

    # Extract field names from #Fields: header
    fields = None
    data_lines = []
    for line in lines:
        if line.startswith('#Fields:'):
            fields = line.strip().split(" ")[1:]
        elif not line.startswith('#'):
            data_lines.append(line.strip().split("\t"))

    if not fields:
        raise ValueError("No #Fields header found in CloudFront log file")
    
    if not data_lines:
        logger.warning("No data lines found in CloudFront log file")
        return [], []

    logger.info(f"Loaded {len(data_lines)} records from CloudFront log")
    return fields, data_lines


def handler(event, context):
    """Lambda handler for SQS event triggers."""
    s3_client = boto3.client("s3")
    
    processed_files = 0
    processed_records = 0
    
    try:
        logger.info("Starting CloudFront log processing from SQS events")
        
        # Process SQS records from the event
        if 'Records' not in event:
            logger.warning("No SQS records found in event")
            return {"statusCode": 200, "body": "No records to process"}
        
        # Collect all file information from SQS messages
        files_to_process = []
        
        for sqs_record in event['Records']:
            try:
                # Parse S3 event from SQS message body
                body = json.loads(sqs_record['body'])
                
                # Handle S3 events wrapped in SQS
                if 'Records' in body:
                    s3_records = body['Records']
                else:
                    s3_records = [body]
                
                for s3_record in s3_records:
                    if 's3' in s3_record:
                        bucket = s3_record['s3']['bucket']['name']
                        key = urllib.parse.unquote_plus(s3_record['s3']['object']['key'], encoding='utf-8')
                        
                        # Only process .gz files
                        if key.endswith('.gz'):
                            files_to_process.append((bucket, key))
                        
            except Exception as e:
                logger.error(f"Failed to parse SQS record: {str(e)}")
                continue
        
        if not files_to_process:
            logger.info("No valid CloudFront log files to process")
            return {"statusCode": 200, "body": "No valid files to process"}
        
        logger.info(f"Processing {len(files_to_process)} CloudFront log files")
        
        # Process each file individually
        for bucket, key in files_to_process:
            try:
                logger.info(f"Processing file: s3://{bucket}/{key}")
                
                # Load the CloudFront log
                fields, data_lines = load_cloudfront_log(s3_client, bucket, key)
                
                if not data_lines:
                    logger.warning(f"No records in {key}")
                    continue
                
                # Check if 'date' field exists
                if 'date' not in fields:
                    logger.error(f"Missing required 'date' column in {key}")
                    continue
                
                date_index = fields.index('date')
                source_filename = os.path.basename(key)
                processed_at = datetime.utcnow().isoformat()
                
                # Add metadata fields
                all_fields = fields + ['processed_at', 'source_file']
                
                # Group data by date for this specific file
                data_by_date = {}
                for row in data_lines:
                    if len(row) > date_index:
                        date_value = row[date_index]
                        if date_value not in data_by_date:
                            data_by_date[date_value] = []
                        
                        # Add metadata to each row
                        row_with_metadata = row + [processed_at, source_filename]
                        data_by_date[date_value].append(row_with_metadata)
                
                # Create separate output files for each date in this input file
                for date_value, rows in data_by_date.items():
                    # Create output filename: original_filename.parquet
                    base_filename = source_filename.replace('.gz', '.parquet')
                    transformed_key = f"{S3_OBJECT_PREFIX}/date={date_value}/{base_filename}"
                    
                    # Create PyArrow table and convert to Parquet
                    table = pa.table([
                        pa.array([row[i] for row in rows])
                        for i in range(len(all_fields))
                    ], names=all_fields)
                    
                    # Drop sensitive/redundant columns
                    columns_to_drop = ['date', 'c-ip']
                    existing_columns_to_drop  = [col for col in columns_to_drop if col in table.schema.names]
                    if existing_columns_to_drop :
                        table = table.drop(existing_columns_to_drop )
                    
                    # Write to Parquet buffer
                    parquet_buffer = BytesIO()
                    pq.write_table(table, parquet_buffer)
                    
                    # Upload to S3
                    s3_client.put_object(
                        Bucket=S3_BUCKET_NAME_TRANSFORMED,
                        Key=transformed_key,
                        Body=parquet_buffer.getvalue(),
                        ContentType='application/octet-stream'
                    )
                    
                    processed_records += len(rows)
                    logger.info(f"Wrote {len(rows)} records for date {date_value} from {source_filename} to s3://{S3_BUCKET_NAME_TRANSFORMED}/{transformed_key}")
                
                processed_files += 1
                
            except Exception as e:
                logger.error(f"Failed to process file {key}: {str(e)}")
                continue
        
    except Exception as e:
        error_msg = f"Failed to process CloudFront logs: {str(e)}"
        logger.error(error_msg)
        return {"statusCode": 500, "body": error_msg}
    
    return {
        "statusCode": 200,
        "body": f"Successfully processed {processed_files} files with {processed_records} records"
    }
