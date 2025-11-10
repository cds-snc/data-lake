import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from google.auth import aws
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
S3_EXPORT_PREFIX = os.environ.get("S3_EXPORT_PREFIX")

# Google Cloud Platform configuration
GCP_PROJECT_NUMBER = os.environ.get("GCP_PROJECT_NUMBER")  # Production: "535589929467"
GCP_POOL_ID = os.environ.get("GCP_POOL_ID")  # Production: "aws-data-warehouse"
GCP_PROVIDER_ID = os.environ.get("GCP_PROVIDER_ID")  # Production: "datalake-production"
GCP_SERVICE_ACCOUNT_EMAIL = os.environ.get("GCP_SERVICE_ACCOUNT_EMAIL")  # Production: "google-analytics-api@platform-core-data-warehouse.iam.gserviceaccount.com"

# Google Analytics Property IDs
GCP_GA_PROPERTY_FORMS_MARKETING_SITE = os.environ.get("GCP_GA_PROPERTY_FORMS_MARKETING_SITE")  # Production: "348891142"
GCP_GA_PROPERTY_NOTIFICATION_GA4 = os.environ.get("GCP_GA_PROPERTY_NOTIFICATION_GA4")  # Production: "307565010"
GCP_GA_PROPERTY_PLATFORM_FORM_CLIENT = os.environ.get("GCP_GA_PROPERTY_PLATFORM_FORM_CLIENT")  # Production: "261232514"
GCP_GA_PROPERTY_PLATFORM_CORE_SUPERSET_DOC = os.environ.get("GCP_GA_PROPERTY_PLATFORM_CORE_SUPERSET_DOC")  # Production: "490027562"

GOOGLE_ANALYTICS_PROPERTIES = {
    "forms_marketing_site": GCP_GA_PROPERTY_FORMS_MARKETING_SITE,
    "notification_ga4": GCP_GA_PROPERTY_NOTIFICATION_GA4,
    "platform_form_client": GCP_GA_PROPERTY_PLATFORM_FORM_CLIENT,
    "platform_core_superset_doc": GCP_GA_PROPERTY_PLATFORM_CORE_SUPERSET_DOC,
}

# Report configurations
REPORT_CONFIGS = [
    {
        "report_name": "daily",
        "dimensions": ["date"],
        "metrics": ["sessions", "activeUsers", "bounceRate", "userEngagementDuration"],
    },
    {
        "report_name": "daily_pages",
        "dimensions": ["date", "pageTitle"],
        "metrics": ["sessions", "activeUsers", "bounceRate", "userEngagementDuration"],
    },
    {
        "report_name": "daily_campaigns",
        "dimensions": ["date", "firstUserManualCampaignName"],
        "metrics": ["sessions", "activeUsers"],
    },
]


def get_google_credentials():
    """Create and return AWS credentials for Google Cloud Workload Identity Federation."""
    return aws.Credentials(
        audience=f"//iam.googleapis.com/projects/{GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/{GCP_POOL_ID}/providers/{GCP_PROVIDER_ID}",
        subject_token_type="urn:ietf:params:aws:token-type:aws4_request",
        token_url="https://sts.googleapis.com/v1/token",
        service_account_impersonation_url=f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{GCP_SERVICE_ACCOUNT_EMAIL}:generateAccessToken",
        credential_source={
            "environment_id": "aws1",
            "region_url": "http://169.254.169.254/latest/meta-data/placement/availability-zone",
            "url": "http://169.254.169.254/latest/meta-data/iam/security-credentials",
            "regional_cred_verification_url": "https://sts.{region}.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15",
        },
    )


def run_ga4_report(client, property_id, dimensions, metrics, start_date="yesterday", end_date="yesterday"):
    """Run a GA4 report and return the rows."""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )
    response = client.run_report(request)

    # Convert response to list of dicts
    dimension_headers = [header.name for header in response.dimension_headers]
    metric_headers = [header.name for header in response.metric_headers]

    rows = []
    for row in response.rows:
        row_dict = {}
        # Add dimensions
        for i, dim in enumerate(row.dimension_values):
            row_dict[dimension_headers[i]] = dim.value
        # Add metrics
        for i, metric in enumerate(row.metric_values):
            row_dict[metric_headers[i]] = metric.value
        rows.append(row_dict)

    return rows


def save_to_s3(data, property_name, report_name):
    """Save data to S3 in JSONL format, partitioned by date from the data itself."""
    if not data:
        logger.info(f"No data to save for {property_name}/{report_name}")
        return []

    # Group records by date
    records_by_date = {}
    for record in data:
        date_value = record.get("date")
        if not date_value:
            logger.warning(f"Record missing date field, skipping: {record}")
            continue
        
        # Convert GA4 date format (YYYYMMDD) to YYYY-MM-DD
        if len(date_value) == 8:
            date_str = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:]}"
        else:
            date_str = date_value
        
        if date_str not in records_by_date:
            records_by_date[date_str] = []
        records_by_date[date_str].append(record)

    # Save each date partition separately
    s3 = boto3.client("s3")
    saved_keys = []
    
    for date_str, records in records_by_date.items():
        # Convert to newline-delimited JSON (JSONL) for Athena
        lines = [json.dumps(record) for record in records]
        content = "\n".join(lines).encode("utf-8")

        # Partition by date: operations/google-analytics/{property}/{report}/date=YYYY-MM-DD/data.json
        s3_key = f"{S3_EXPORT_PREFIX}/{property_name}/{report_name}/date={date_str}/data.json"

        try:
            s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=content,
                ContentType="application/json",
            )
            logger.info(f"Saved {len(records)} records to s3://{S3_BUCKET_NAME}/{s3_key}")
            saved_keys.append(s3_key)
        except Exception as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")
    
    return saved_keys


def handler(event, context):
    """Google Analytics data export handler."""
    logger.info("Starting Google Analytics export")

    try:
        # Initialize Google Analytics client with AWS credentials
        credentials = get_google_credentials()
        client = BetaAnalyticsDataClient(credentials=credentials)

        results = {}

        # Process each GA4 property
        for property_name, property_id in GOOGLE_ANALYTICS_PROPERTIES.items():
            logger.info(f"Processing property: {property_name} (ID: {property_id})")
            
            try:
                property_results = {}
                
                # Fetch data for each report configuration
                for config in REPORT_CONFIGS:
                    report_name = config["report_name"]
                    data = run_ga4_report(
                        client,
                        property_id,
                        dimensions=config["dimensions"],
                        metrics=config["metrics"],
                        start_date="yesterday",
                        end_date="yesterday"
                    )
                    logger.info(f"Fetched {len(data)} records for {report_name}")
                    
                    # Save each report separately to S3, partitioned by date from data
                    s3_keys = save_to_s3(data, property_name, report_name)
                    property_results[report_name] = {"records": len(data), "s3_keys": s3_keys}
                
                results[property_name] = property_results
                
            except Exception as e:
                logger.error(f"Failed to process property {property_name}: {str(e)}")
                results[property_name] = {"error": str(e)}

        logger.info("Google Analytics export completed successfully")
        return {"statusCode": 200, "body": json.dumps(results)}

    except Exception as e:
        logger.error(f"Google Analytics export failed: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}