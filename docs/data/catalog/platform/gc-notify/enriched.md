# Platform / GC Notify / Enriched Notifications

Enriched dataset combining notification event data with service and template context. This curated dataset provides a single, denormalized view of notifications with complete metadata for analysis and reporting.

Each row represents a single notification (sent or historical) enriched with service details (name, limits, organization) and template information (name, category, sending vehicle).

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the Physical dataset: `platform_gc_notify_notifications_enriched`.

`Keywords`: Platform, GC Notify, Notifications, Enriched, Denormalized, Service, Template

---

[:information_source: View the data pipeline](../../../pipelines/platform/gc-notify/enriched.md)

## Provenance

This dataset is created daily by enriching core notification data with service and template metadata through a Glue ETL job. The enrichment process joins notifications with services and templates to provide complete context for each notification event.

* `Updated`: Daily
* `Steward`: Platform Core Services
* `Contact`: Slack channel #platform-core-services
```
cds-data-lake-transformed-production/platform/gc-notify/notifications_enriched/year=YYYY/month=YYYY-MM/*.parquet
```

## Fields

The enriched notifications table combines fields from three sources: notification events, services, and templates.

### Notification Event Fields

| Field | Type | Description |
|-------|------|-------------|
| notification_id | string | Unique identifier for the notification event. |
| notification_created_at | timestamp | Date and time when the notification was created. |
| notification_updated_at | timestamp | Date and time when the notification was last updated. |
| notification_sent_at | timestamp | Date and time when the notification was sent. |
| notification_status | string | Current status of the notification. |
| notification_type | string | Type of notification: email or sms. |
| notification_billable_units | integer | Number of billable units consumed by this notification. |
| notification_queue_name | string | Name of the processing queue this notification was handled by. |
| notification_reference | string | AWS provided message ID or reference identifier. |
| job_id | string | Foreign key reference to the batch job that created this notification. |
| api_key_id | string | Foreign key reference to the API key used to create this notification. |
| api_key_type | string | Type of API key used. |
| sms_total_message_price | double | Total cost charged for the SMS message. |
| sms_total_carrier_fee | double | Carrier fee portion of the total SMS cost. |
| sms_iso_country_code | string | ISO country code for SMS destination. |
| sms_carrier_name | string | Name of the SMS carrier that delivered the message. |
| sms_message_encoding | string | Character encoding used for the SMS. |
| sms_origination_phone_number | string | Phone number that sent the SMS. |

### Service Context Fields

| Field | Type | Description |
|-------|------|-------------|
| service_id | string | Unique identifier for the GC Notify service. |
| service_name | string | Name of the service that sent this notification. |
| service_active | boolean | Whether the service is currently active. |
| service_count_as_live | boolean | Whether this service counts as a live production service. |
| service_go_live_at | timestamp | Date and time when the service went live. |
| service_message_limit | integer | Maximum number of messages this service can send. |
| service_restricted | boolean | Whether this is a trial/restricted service. |
| service_rate_limit | integer | Maximum number of notifications per time unit. |
| service_sms_daily_limit | integer | Maximum SMS messages per day for this service. |
| organisation_id | string | Foreign key reference to the organization. |
| organisation_name | string | Name of the organization operating this service. |

### Template Context Fields

| Field | Type | Description |
|-------|------|-------------|
| template_id | string | Unique identifier for the notification template. |
| template_name | string | Name of the notification template used. |
| template_created_at | timestamp | Date and time when the template was created. |
| template_updated_at | timestamp | Date and time when the template was last updated. |
| template_version | integer | Version number of the template used. |
| template_category_id | string | Foreign key reference to the template category. |
| tc_name_en | string | English name of the template category. |
| tc_name_fr | string | French name of the template category. |
| tc_email_process_type | string | Processing priority for email templates in this category. |
| tc_sms_process_type | string | Processing priority for SMS templates in this category. |
| tc_sms_sending_vehicle | string | SMS sending vehicle for this category (long_code or short_code). |

### Partition Fields

| Field | Type | Description |
|-------|------|-------------|
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

## Notes

**Data Sources**: This enriched table combines data from three GC Notify tables:
- `platform_gc_notify_notifications`: Current notifications within retention period
- `platform_gc_notify_notification_history`: Historical record of all past notifications
- `platform_gc_notify_services`: Service metadata and configuration
- `platform_gc_notify_templates`: Template definitions and metadata
- `platform_gc_notify_template_categories`: Template category information

**Denormalization**: This is a denormalized, curated table designed for analysis. All service and template attributes are included in each row for easy querying without requiring joins. This makes the table larger but simplifies analysis queries.

**Notification Coverage**: The enriched table includes both current notifications (from `notifications` table) and historical notifications (from `notification_history` table) to provide a complete view of all past and present notification events.

**Partition Strategy**: Data is partitioned by year and month based on notification creation date, allowing efficient month-based queries and incremental processing.

**Enrichment Process**: The enrichment job runs daily and processes the current and previous month's data to ensure that any updates to services or templates are reflected in the enriched view.
