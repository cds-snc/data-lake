# Operations / Google Analytics

Dataset describing Google Analytics web traffic metrics across CDS web properties including aggregated daily metrics, campaign performance, and page-level statistics.

Each row represents daily analytics data aggregated by Google Analytics property, optionally broken down by campaign or page, providing insights into user engagement, session activity, and web performance.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as Physical datasets: `operations_google_analytics_daily`, `operations_google_analytics_daily_campaigns`, and `operations_google_analytics_daily_pages`.

`Keywords`: Google Analytics, web traffic, user engagement, sessions, pages, campaigns, metrics, analytics, website performance

---

[:information_source: View the data pipeline](../../../pipelines/operations/googleanalytics/google-analytics.md)

## Provenance

This dataset is extracted daily from Google Analytics 4 properties using the Google Analytics Reporting API. The data is transformed through AWS Glue ETL jobs that normalize data across multiple GA properties and aggregate metrics. Three separate data aggregations are produced:
- **Daily Aggregated Metrics**: Overall platform performance metrics aggregated by date
- **Daily Campaign Performance**: Campaign-level performance metrics including sessions and active users by campaign
- **Daily Page Performance**: Page-level performance metrics including bounce rate and engagement duration by page

More documentation on the pipeline can be found [here](../../../pipelines/operations/googleanalytics/google-analytics.md).

* `Schedule`: Daily
* `Steward`: Platform Core Services
* `Contact`: Slack channel #platform-core-services

## Fields

The dataset is split into three tables, all derived from Google Analytics data exported via API.

### Table 1: Daily Aggregated Metrics (`operations_google_analytics_daily`)

Data about overall daily platform performance across Google Analytics properties. Each row represents a single day's aggregated metrics for a specific GA property.

| Field Name | Type | Description |
|------------|------|-------------|
| ga_property | string | Google Analytics property identifier (e.g., "platform_core_superset_doc", "platform_form_client", "forms_marketing_site", "notification_ga4") |
| date | date | Date for which the metrics are aggregated (YYYY-MM-DD format) |
| sessions | int | Total number of sessions for the property on this date |
| activeUsers | int | Number of unique active users for the property on this date |
| bounceRate | double | Bounce rate as a percentage (0-100), the percentage of sessions that ended on the first page |
| userEngagementDuration | int | Average duration in seconds of user engagement with the property |

### Table 2: Daily Campaign Performance (`operations_google_analytics_daily_campaigns`)

Data about daily campaign performance across Google Analytics properties. Each row represents metrics for a specific campaign on a specific date.

| Field Name | Type | Description |
|------------|------|-------------|
| ga_property | string | Google Analytics property identifier (e.g., "platform_core_superset_doc", "platform_form_client", "forms_marketing_site", "notification_ga4") |
| date | date | Date for which the campaign metrics are aggregated (YYYY-MM-DD format) |
| firstUserManualCampaignName | string | Name of the manual campaign assigned to the first user interaction |
| sessions | int | Total number of sessions attributed to this campaign on this date |
| activeUsers | int | Number of unique active users who came from this campaign on this date |

### Table 3: Daily Page Performance (`operations_google_analytics_daily_pages`)

Data about daily page-level performance across Google Analytics properties. Each row represents metrics for a specific page on a specific date.

| Field Name | Type | Description |
|------------|------|-------------|
| ga_property | string | Google Analytics property identifier (e.g., "platform_core_superset_doc", "platform_form_client", "forms_marketing_site", "notification_ga4") |
| date | date | Date for which the page metrics are aggregated (YYYY-MM-DD format) |
| pageTitle | string | Title of the page as captured by Google Analytics |
| sessions | int | Total number of sessions that included this page on this date |
| activeUsers | int | Number of unique active users who visited this page on this date |
| bounceRate | double | Bounce rate for this specific page as a percentage (0-100) |
| userEngagementDuration | int | Average engagement duration in seconds for this specific page |

## Notes

**Data Sources**: This dataset includes data from four Google Analytics 4 properties:
1. `platform_core_superset_doc` - Superset documentation and analytics platform
2. `platform_form_client` - GC Forms client application
3. `forms_marketing_site` - Forms marketing website
4. `notification_ga4` - Notification service analytics

**GA Properties**: Data is normalized and standardized across all GA properties. The `ga_property` field identifies which GA property the metrics came from, allowing for property-specific analysis or cross-property comparisons.

**Metric Definitions**:
- **Sessions**: A session is a group of user interactions that take place within a given time frame
- **Active Users**: Users who had at least one session during the reporting period
- **Bounce Rate**: The percentage of sessions that terminated on the first page without any interaction beyond the initial page view
- **Engagement Duration**: Average time users spent actively engaged with content during a session

**Data Normalization**: The ETL process performs the following transformations:
- Normalizes date formats from YYYYMMDD to YYYY-MM-DD
- Converts string representations of numbers to appropriate numeric types (int, double)
- Handles empty string values by converting them to null
- Unifies data formats across multiple GA property sources
- Normalizes field names to consistent camelCase naming conventions

**Data Quality**: Empty string values in numeric fields are converted to null during ETL processing to maintain data integrity. All metrics are aggregated at the daily level and are non-negative values.

**Campaign and Page Data**: Campaign and page metrics are only available when the respective dimensions had trackable activity on the given date. Campaigns and pages with no activity on a specific date will not appear as rows for that date.
