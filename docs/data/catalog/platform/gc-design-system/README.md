# GC Design System Data Catalog

## Overview
The GC Design System data catalog contains information from multiple sources related to the adoption, usage, and performance of the Government of Canada Design System.

## Available Datasets

### [Airtable Client Data](./airtable.md)
Client and department data collected through Airtable forms, providing insights into who is using the design system and their implementation status.

- **Update Frequency**: Daily (6:00 AM UTC)
- **Processing**: Scheduled Lambda function
- **Data Type**: Client registrations, implementation feedback

### [NPM Download Statistics](./npm.md) 
Download statistics for the `@cdssnc/gcds-components-vue` NPM package, showing adoption trends and usage patterns.

- **Update Frequency**: Daily (6:00 AM UTC)  
- **Processing**: Scheduled Lambda function
- **Data Type**: Package download counts by time period

### [CloudFront Access Logs](./cloudfront.md)
Real-time processed CloudFront access logs providing detailed insights into CDN usage, performance, and user behavior.

- **Update Frequency**: Real-time (S3 triggered)
- **Processing**: Event-driven Lambda function
- **Data Type**: HTTP requests, geographic distribution, performance metrics

## Data Architecture

### Processing Patterns
- **Scheduled Processing**: Airtable and NPM data use scheduled Lambda functions with daily cron triggers
- **Event-Driven Processing**: CloudFront logs use S3 event triggers for real-time processing
- **Schema Management**: Glue crawlers automatically update table schemas after data processing

### Storage Structure
All data is stored in the S3 data lake with the following structure:
```
s3://cds-data-lake-transformed-production/platform/gc-design-system/
├── airtable/          # Client and department data
├── npm/               # Package download statistics  
└── cloudfront-logs/   # CDN access logs
```

### Data Quality
- All datasets include processing timestamps for audit trails
- Error handling prevents individual failures from affecting other data sources
- Data is partitioned by date for efficient querying

## Common Queries

### Design System Adoption Overview
```sql
-- Combine client registrations with download trends
SELECT 
  a.date_modified,
  a.department,
  a.implementation_status,
  n.downloads as downloads
FROM platform_gc_design_system_airtable a
LEFT JOIN platform_gc_design_system_npm n 
  ON DATE(a.date_modified) = DATE(n.day)
WHERE a.date_modified >= current_date - interval '30' day
ORDER BY a.date_modified DESC;
```

### Performance and Usage Correlation
```sql
-- Correlate NPM downloads with CDN traffic
SELECT 
  DATE(c.date) as date,
  COUNT(c.*) as cdn_requests,
  AVG(n.downloads) as avg_daily_downloads
FROM platform_gc_design_system_cloudfront_logs c
LEFT JOIN platform_gc_design_system_npm n 
  ON DATE(c.date) = DATE(n.day)
WHERE DATE(c.date) >= current_date - interval '7' day
GROUP BY DATE(c.date)
ORDER BY date;
```

## Data Access
- **Database**: `platform_gc_design_system`
- **Query Interface**: AWS Athena
- **Visualization**: Available through standard BI tools

## Related Documentation
- [Pipeline Documentation](../../../pipelines/platform/gc-design-system/) - Technical implementation details
- [Data Architecture](../../architecture/) - Overall data lake design
- [Query Examples](./examples/) - Additional sample queries

## Contact
For questions about GC Design System data or access issues, contact the GC Design System team.
