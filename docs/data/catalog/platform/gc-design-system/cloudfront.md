# Platform / GC Design System / CloudFront

CloudFront access logs dataset containing detailed web analytics data for the Government of Canada Design System website.

Each row represents a single HTTP request made to the CloudFront distribution serving the GC Design System, including request details, performance metrics, and geographic information.

This dataset is processed through the [CloudFront Log Processing Pipeline](../../pipelines/platform/gc-design-system/cloudfront.md) using event-driven architecture for real-time insights.

`Keywords`: CloudFront, CDN, web analytics, access logs, performance, traffic, GC Design System

## Provenance

This dataset is derived from AWS CloudFront access logs generated automatically when users access the GC Design System website. The raw compressed log files (.gz format) are processed in real-time using an event-driven Lambda function that converts them to optimized Parquet format with date-based partitioning.

* `Updated`: Real-time (event-driven processing when logs are uploaded)
* `Steward`: GC Design System team
* `Contact`: Slack channel #ds-cds-internal
* `Location`: `s3://cds-data-lake-transformed-production/platform/gc-design-system/cloudfront-logs/`

## Fields

Sample data showing typical CloudFront access log entries converted to Parquet format:

| Field Name | Type | Description |
|-------|------|-------------|
| date | string | **Partition Key** Request date in YYYY-MM-DD format |
| time | string | Request time in HH:MM:SS format (UTC) |
| x-edge-location | string | CloudFront edge location code that served the request (e.g., "IAD89-C1") |
| sc-bytes | string | Number of bytes sent from CloudFront to the client |
| cs-method | string | HTTP method used for the request, one of "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS" |
| cs(host) | string | Host header from the request |
| cs-uri-stem | string | URI path portion of the request (without query parameters) |
| sc-status | string | HTTP status code returned by CloudFront (e.g., "200", "404", "403") |
| cs(referer) | string | Referer header from the request, indicating the page that linked to this resource |
| cs(user-agent) | string | User agent string from the client browser |
| cs-uri-query | string | Query string parameters from the request URL |
| cs(cookie) | string | Cookie header from the request |
| x-edge-result-type | string | Result type for the request, one of "Hit", "Miss", "RefreshHit", "OriginShield" |
| x-edge-request-id | string | Unique identifier for the request assigned by CloudFront |
| x-host-header | string | Host header from the request |
| cs-protocol | string | Protocol used for the request, either "http" or "https" |
| cs-bytes | string | Number of bytes in the client request |
| time-taken | string | Time in seconds that CloudFront spent processing the request |
| x-forwarded-for | string | X-Forwarded-For header if present in the request |
| ssl-protocol | string | SSL/TLS protocol version if HTTPS was used |
| ssl-cipher | string | SSL/TLS cipher used if HTTPS was used |
| x-edge-response-result-type | string | Response result type from CloudFront edge |
| cs-protocol-version | string | HTTP protocol version used by the client |
| fle-status | string | Field-level encryption status |
| fle-encrypted-fields | string | Number of field-level encrypted fields |
| c-port | string | Port number used by the client for the request |
| time-to-first-byte | string | Time in seconds from request to first response byte |
| x-edge-detailed-result-type | string | Additional details about the result type |
| sc-content-type | string | Content-Type header in the response |
| sc-content-len | string | Content-Length header in the response |
| sc-range-start | string | Range start value if this was a range request |
| sc-range-end | string | Range end value if this was a range request |
| processed_at | string | When the log entry was processed by the Lambda function |
| source_file | string | Original CloudFront log filename for audit trail |

## Notes

**Data Processing**: CloudFront logs are processed using an event-driven architecture that provides near real-time availability. When CloudFront uploads log files to S3, they immediately trigger SQS messages that invoke Lambda processing within minutes.

**Schema Completeness**: The schema includes all standard CloudFront access log fields. Note that some fields (like SSL-related fields) may be empty for HTTP requests, and field-level encryption fields are typically unused unless specifically configured.

**Partitioning Strategy**: Data is partitioned by the actual request date from the CloudFront logs (not the processing date), ensuring accurate time-based queries and efficient storage organization.

**Schema Discovery**: The Glue crawler runs on a daily schedule at 6:00 AM UTC (Production only) to automatically discover and update the table schema as new data is processed. This ensures the catalog stays current with any schema changes while maintaining independence from the real-time processing pipeline.
