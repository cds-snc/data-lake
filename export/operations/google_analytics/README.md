# Google Analytics Export Lambda

## Overview

This Lambda function exports Google Analytics 4 (GA4) data to the Data Lake's S3 raw bucket. It runs on a scheduled basis and fetches data for 4 different GA4 properties, saving the data in a partitioned format suitable for Athena queries.

## Architecture

### Authentication
- Uses **Google Workload Identity Federation** to authenticate from AWS to Google Cloud
- No API keys or service account keys stored - uses the Lambda's IAM role credentials
- AWS credentials are automatically exchanged for Google Cloud credentials via OIDC

### Data Flow
1. Lambda is triggered on schedule (via EventBridge)
2. Authenticates to Google Cloud using Workload Identity Federation
3. Fetches GA4 data for yesterday's date (data is delayed by 1 day)
4. Saves data to S3 in JSONL format, partitioned by date
5. Returns summary of processed records

## GA4 Properties

The function exports data from 4 properties:
- `forms_marketing_site` (ID: 348891142)
- `notification_ga4` (ID: 307565010)
- `platform_form_client` (ID: 261232514)
- `platform_core_superset_doc` (ID: 490027562)

## Reports Generated

For each property, 3 reports are generated daily:

### 1. Daily Stats
- **Dimensions**: date
- **Metrics**: sessions, activeUsers, bounceRate, userEngagementDuration
- **S3 Path**: `operations/google-analytics/{property}/daily_stats/date=YYYY-MM-DD/data.json`

### 2. Daily Page Stats
- **Dimensions**: date, pageTitle
- **Metrics**: sessions, activeUsers, bounceRate, userEngagementDuration
- **S3 Path**: `operations/google-analytics/{property}/daily_page_stats/date=YYYY-MM-DD/data.json`

### 3. Daily Source Stats
- **Dimensions**: date, firstUserManualCampaignName
- **Metrics**: sessions, activeUsers
- **S3 Path**: `operations/google-analytics/{property}/daily_source_stats/date=YYYY-MM-DD/data.json`

## S3 Data Structure

```
s3://raw-bucket/operations/google-analytics/
├── forms_marketing_site/
│   ├── date=2024-11-10/
│   │       └── data.json
│   ├── date=2024-11-10/
│   │       └── data.json
│   └── date=2024-11-10/
│           └── data.json
├── notification_ga4/
│   └── ...
├── platform_form_client/
│   └── ...
└── platform_core_superset_doc/
    └── ...
```

## Data Format

Data is stored in **JSONL format** (newline-delimited JSON), where each line is a valid JSON object representing one row of data.

Example:
```json
{"date":"20241110","sessions":"1523","activeUsers":"1204","bounceRate":"0.42","userEngagementDuration":"234.5"}
{"date":"20241110","sessions":"892","activeUsers":"701","bounceRate":"0.38","userEngagementDuration":"198.3"}
```

This format is:
- Efficient for large datasets
- Compatible with AWS Athena
- Easy to process with standard tools

## Environment Variables

- `S3_BUCKET_NAME`: Target S3 bucket for exports (raw bucket)
- `S3_EXPORT_PREFIX`: Prefix for S3 keys (default: `operations/google-analytics`)

## IAM Permissions

The Lambda requires:
- `s3:PutObject` - Write data to S3
- `s3:PutObjectAcl` - Set object permissions
- `s3:ListBucket` - List bucket contents (with prefix restriction)

## Google Cloud Configuration

### Workload Identity Federation Settings
- **Project Number**: 535589929467
- **Pool ID**: aws-data-warehouse
- **Provider ID**: datalake-production
- **Service Account**: google-analytics-api@platform-core-data-warehouse.iam.gserviceaccount.com

## Dependencies

- `boto3` - AWS SDK
- `google-analytics-data` - Google Analytics Data API client
- `google-auth` - Google authentication library with AWS support

## Testing

Run tests with:
```bash
pytest main_test.py -v
```


## Monitoring

The Lambda logs:
- Start/completion messages
- Number of records processed per report
- S3 paths where data is saved
- Any errors encountered during processing

Check CloudWatch Logs for execution details.

## Error Handling

- Each property is processed independently - if one fails, others continue
- Each report type is processed independently - if one fails, others continue
- Detailed error messages are logged and returned in the response
- Function returns HTTP 500 only if the entire execution fails (e.g., authentication)

## Future Enhancements

Potential improvements:
- Add Glue crawler to automatically catalog the data
- Support for custom date ranges via event parameters
- Additional report types (traffic sources, devices, etc.)
- Retry logic for transient Google API errors
- CloudWatch metrics for data volume and API usage
