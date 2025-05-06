# Platform / GC Notify

Dataset providing GC Notify data.  There are fourteen tables as part of this dataset:

- `jobs`: Batch jobs for email and SMS notification sending
- `login_events`: Records of user login activity
- `notification_history`: Historical record of all notifications
- `notifications`: Core table containing email and SMS notifications within their service's retention period
- `organisation`: Organizations that use GC Notify
- `permissions`: User permissions that determine access levels within the system
- `services`: Notification services used to send communications
- `services_history`: Historical record of changes made to notification services
- `template_categories`: Categories for organizing notification templates
- `templates`: Email and SMS templates used for sending notifications
- `templates_history`: Historical record of changes made to notification templates
- `user_to_organisation`: Mapping between users and their organizations
- `user_to_service`: Mapping between users and their services
- `users`: Users accounts within the system

No personally identifiable information (PII) is included as part of this dataset.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the following Physical datasets:

- `platform_gc_notify_jobs`
- `platform_gc_notify_login_events`
- `platform_gc_notify_notification_history`
- `platform_gc_notify_notifications`
- `platform_gc_notify_organisation`
- `platform_gc_notify_permissions`
- `platform_gc_notify_services`
- `platform_gc_notify_services_history`
- `platform_gc_notify_template_categories`
- `platform_gc_notify_templates`
- `platform_gc_notify_templates_history`
- `platform_gc_notify_user_to_organisation`
- `platform_gc_notify_user_to_service`
- `platform_gc_notify_users`

`Keywords`: Platform, GC Notify

---

[:information_source:  View the data pipeline](../../../pipelines/platform/gc-notify/export.md)

## Provenance

This dataset is exported daily from the GC Notify database's automated snapshots. More documentation on the pipeline can be found [here](../../../pipelines/platform/gc-notify/export.md).

* `Updated`: Daily
* `Steward`: GC Notify
* `Contact`: [Jimmy Royer](mailto:jimmy.royer@cds-snc.ca)
* `Location`: 
```
cds-data-lake-transformed-production/platform/gc-notify/jobs/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/login_events/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/notification_history/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/notifications/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/organisation/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/permissions/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/services/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/services_history/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/template_categories/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/templates/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/templates_history/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/user_to_organisation/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/user_to_service/year=YYYY/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-notify/users/year=YYYY/month=YYYY-MM/*.parquet
```

## Fields

All fields are sourced directly from the GC Notify database tables.

[Queries to return example data](examples/export.sql) have also been provided.

Here's a descriptive list of the fields in each table:

### Table: platform_gc_notify_jobs

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for each job. Primary key for the table. |
| original_file_name | varchar | Name of the file that was uploaded to create this job. |
| service_id | uuid | Foreign key linking to the service running the job. |
| template_id | uuid | Foreign key referencing the template used for notifications in this job. |
| created_at | timestamp | Date and time when the job was created. |
| updated_at | timestamp | Date and time when the job was last updated. |
| notification_count | integer | Total number of notifications to be sent in this job. |
| notifications_sent | integer | Number of notifications that have been sent. |
| processing_started | timestamp | Date and time when the job started being processed. |
| processing_finished | timestamp | Date and time when the job finished processing. |
| created_by_id | uuid | Foreign key referencing the user who created this job. |
| template_version | integer | Version number of the template used for this job. |
| notifications_delivered | integer | Number of notifications successfully delivered to recipients. |
| notifications_failed | integer | Number of notifications that failed to deliver. |
| job_status | varchar | Status of the job. |
| scheduled_for | timestamp | Date and time when the job is scheduled to run, for delayed notifications. |
| archived | bool | Flag indicating whether the job has been archived. |
| api_key_id | uuid | Foreign key referencing the API key used to create this job. |
| sender_id | uuid | Sender identity used for this job. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_login_events

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for each login event |
| user_id | uuid | Foreign key referencing the user that logged in. |
| created_at | timestamp | Date and time when the login event was created. |
| updated_at | timestamp | Date and time when the login event was updated. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_notification_history

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for each notification record. |
| job_id | uuid | Foreign key reference to the batch job that generated this notification. |
| job_row_number | integer | Sequential number indicating the position of this notification within its parent job. |
| service_id | uuid | Foreign key reference to the service that sent the notification. |
| template_id | uuid | Foreign key reference to the message template used for this notification. |
| template_version | integer | Version number of the template used. |
| api_key_id | uuid | Foreign key reference to the API key used to authenticate the notification request. |
| key_type | varchar | Type of API key used. |
| notification_type | notification_type | Categorization of notification (email or sms). |
| created_at | timestamp | Date and time when the notification record was created. |
| sent_at | timestamp | Date and time when the notification was sent. |
| updated_at | timestamp | Date and time when the notification record was updated. |
| reference | varchar | AWS provided message ID of the notification. |
| billable_units | integer | Number of billing units consumed by this notification. For SMS this is the number of message fragments. |
| client_reference | varchar | Customer-provided reference for their own tracking purposes. |
| international | bool | Flag indicating whether the notification was sent internationally. |
| phone_prefix | varchar | Country code prefix for phone numbers in SMS notifications. |
| rate_multiplier | numeric | Pricing multiplier applied to SMS notifications based on the billable_units. |
| notification_status | text | Status of the notification. |
| created_by_id | uuid | Identifier for the user that initiated the notification. |
| queue_name | text | Name of the processing queue this notification was handled by. |
| feedback_type | notification_feedback_types | Category of delivery feedback received. |
| feedback_subtype | notification_feedback_subtypes | More specific feedback classification. |
| ses_feedback_id | varchar | Amazon SES specific feedback identifier for email notifications. |
| ses_feedback_date | timestamp | Date and time when feedback was received from Amazon SES. |
| sms_total_message_price | float | Total cost charged for the SMS message. |
| sms_total_carrier_fee | float | Portion of the total cost that goes to the carrier. |
| sms_iso_country_code | varchar | ISO country code for the destination of the SMS. |
| sms_carrier_name | varchar | Name of the carrier that delivered the SMS message. |
| sms_message_encoding | varchar | Character encoding used for the SMS message. |
| sms_origination_phone_number | varchar | Phone number that sent the SMS message. |
| feedback_reason | varchar | Pinpoint failure reason when an SMS message cannot be delivered. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_notifications

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for each notification record. |
| job_id | uuid | Foreign key reference to the batch job that generated this notification. |
| job_row_number | integer | Sequential number indicating the position of this notification within its parent job. |
| service_id | uuid | Foreign key reference to the service that sent the notification. |
| template_id | uuid | Foreign key reference to the message template used for this notification. |
| template_version | integer | Version number of the template used. |
| api_key_id | uuid | Foreign key reference to the API key used to authenticate the notification request. |
| key_type | varchar | Type of API key used. |
| notification_type | notification_type | Categorization of notification (email or sms). |
| created_at | timestamp | Date and time when the notification record was created. |
| sent_at | timestamp | Date and time when the notification was sent. |
| updated_at | timestamp | Date and time when the notification record was updated. |
| reference | varchar | AWS provided message ID of the notification. |
| billable_units | integer | Number of billing units consumed by this notification. For SMS this is the number of message fragments. |
| client_reference | varchar | Customer-provided reference for their own tracking purposes. |
| international | bool | Flag indicating whether the notification was sent internationally. |
| phone_prefix | varchar | Country code prefix for phone numbers in SMS notifications. |
| rate_multiplier | numeric | Pricing multiplier applied to SMS notifications based on the billable_units. |
| notification_status | text | Status of the notification. |
| created_by_id | uuid | Identifier for the user that initiated the notification. |
| queue_name | text | Name of the processing queue this notification was handled by. |
| feedback_type | notification_feedback_types | Category of delivery feedback received. |
| feedback_subtype | notification_feedback_subtypes | More specific feedback classification. |
| ses_feedback_id | varchar | Amazon SES specific feedback identifier for email notifications. |
| ses_feedback_date | timestamp | Date and time when feedback was received from Amazon SES. |
| sms_total_message_price | float | Total cost charged for the SMS message. |
| sms_total_carrier_fee | float | Portion of the total cost that goes to the carrier. |
| sms_iso_country_code | varchar | ISO country code for the destination of the SMS. |
| sms_carrier_name | varchar | Name of the carrier that delivered the SMS message. |
| sms_message_encoding | varchar | Character encoding used for the SMS message. |
| sms_origination_phone_number | varchar | Phone number that sent the SMS message. |
| feedback_reason | varchar | Pinpoint failure reason when an SMS message cannot be delivered. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_organisation

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for the organisation. |
| name | varchar | Name of the organisation. |
| active | bool | Indicates whether the organisation is currently active in the system. |
| created_at | timestamp | Date and time when the organisation record was created. |
| updated_at | timestamp | Date and time when the organisation record was last updated. |
| email_branding_id | uuid | Email branding configuration used by this organisation. |
| agreement_signed | bool | Indicates whether the organisation has signed the service agreement. |
| agreement_signed_at | timestamp | Date and time when the service agreement was signed. |
| agreement_signed_by_id | uuid | Foreign key reference to the user who signed the service agreement. |
| agreement_signed_version | float | Version number of the service agreement that was signed |
| crown | bool | Indicates whether this is a Crown Corporation. |
| organisation_type | varchar | Type of the organisation. |
| default_branding_is_french | bool | Indicates whether the default branding for this organisation uses French. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_permissions

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for the permission. |
| service_id | uuid | Foreign key reference to the service this permission applies to. |
| user_id | uuid | Foreign key reference to the user the permission has been granted to. |
| permission | permission_types | The permission that has been granted. |
| created_at | timestamp | Date and time when the permission was assigned. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_services

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for the service. |
| name | varchar | Name of the service. |
| created_at | timestamp | Date and time when the service was created. |
| updated_at | timestamp | Date and time when the service was last updated. |
| active | bool | Indicates whether the service is currently active. |
| message_limit | integer | Maximum number of messages this service can send. |
| restricted | bool | Indicates if this is a trial service. |
| email_from | text | Email address that appears in the "From" field when sending email notifications. |
| created_by_id | uuid | Identifier of the user who created this service. |
| version | integer | Current version of the service configuration. |
| research_mode | bool | Indicates if this service is in research mode. |
| organisation_type | varchar | Type of organisation this service is classified as. |
| prefix_sms | bool | Whether SMS messages should include a prefix identifying the service. |
| crown | bool | Indicates if this service is operated by a Crown Corporation. |
| rate_limit | integer | Maximum number of notifications the service can send per time unit. |
| consent_to_research | bool | Whether the service has consented to being included in research studies. |
| volume_email | integer | Anticipated volume of email notifications for this service. |
| volume_sms | integer | Anticipated volume of SMS notifications for this service. |
| count_as_live | bool | Whether this service should be counted as a live production service. |
| go_live_at | timestamp | Date and time when this service went live. |
| go_live_user_id | uuid | Identifier of the user who requested the service to go live. |
| organisation_id | uuid | Reference to the organisation that this service belongs to. |
| sending_domain | text | Domain name used for sending email notifications. |
| default_branding_is_french | bool | Whether the default branding for notifications is in French. |
| sms_daily_limit | integer | Maximum number of SMS messages this service can send per day. |
| organisation_notes | varchar | Additional notes about the organisation in relation to this service. |
| sensitive_service | bool | Indicates if this service handles sensitive or protected information. |
| email_annual_limit | integer | Maximum number of email notifications this service can send annually. |
| sms_annual_limit | integer | Maximum number of SMS notifications this service can send annually. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_services_history

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for the service. |
| name | varchar | Name of the service. |
| created_at | timestamp | Date and time when the service was created. |
| updated_at | timestamp | Date and time when the service was last updated. |
| active | bool | Indicates whether the service is currently active. |
| message_limit | integer | Maximum number of messages this service can send. |
| restricted | bool | Indicates if this is a trial service. |
| email_from | text | Email address that appears in the "From" field when sending email notifications. |
| created_by_id | uuid | Identifier of the user who created this service. |
| version | integer | Current version of the service configuration. |
| research_mode | bool | Indicates if this service is in research mode. |
| organisation_type | varchar | Type of organisation this service is classified as. |
| prefix_sms | bool | Whether SMS messages should include a prefix identifying the service. |
| crown | bool | Indicates if this service is operated by a Crown Corporation. |
| rate_limit | integer | Maximum number of notifications the service can send per time unit. |
| consent_to_research | bool | Whether the service has consented to being included in research studies. |
| volume_email | integer | Anticipated volume of email notifications for this service. |
| volume_sms | integer | Anticipated volume of SMS notifications for this service. |
| count_as_live | bool | Whether this service should be counted as a live production service. |
| go_live_at | timestamp | Date and time when this service went live. |
| go_live_user_id | uuid | Identifier of the user who requested the service to go live. |
| organisation_id | uuid | Reference to the organisation that this service belongs to. |
| sending_domain | text | Domain name used for sending email notifications. |
| default_branding_is_french | bool | Whether the default branding for notifications is in French. |
| sms_daily_limit | integer | Maximum number of SMS messages this service can send per day. |
| organisation_notes | varchar | Additional notes about the organisation in relation to this service. |
| sensitive_service | bool | Indicates if this service handles sensitive or protected information. |
| email_annual_limit | integer | Maximum number of email notifications this service can send annually. |
| sms_annual_limit | integer | Maximum number of SMS notifications this service can send annually. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_template_categories

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for the template category. |
| name_en | varchar | English name of the template category. |
| name_fr | varchar | French name of the template category. |
| description_en | varchar | English description of what this template category is used for. |
| description_fr | varchar | French description of what this template category is used for. |
| sms_process_type | varchar | Defines the processing priority of SMS templates in this category. |
| email_process_type | varchar | Defines the processing priority of email templates in this category. |
| hidden | bool | Indicates whether this category should be hidden in the interface. |
| created_at | timestamp | Date and time when this template category was created. |
| updated_at | timestamp | Date and time when this template category was last updated. |
| sms_sending_vehicle | sms_sending_vehicle | Defines if templates in this category use a short or long code for sending. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_templates

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for the notification template. |
| name | varchar | Name of the template. |
| template_type | template_type | Categorization of the template (email or sms). |
| created_at | timestamp | Date and time when the template was created. |
| updated_at | timestamp | Date and time when the template was last modified. |
| service_id | uuid | Foreign key reference to the service that owns this template. |
| created_by_id | uuid | Foreign key reference to the user who created the template. |
| version | integer | Version number of the template. |
| archived | bool | Indicates whether the template has been archived and is no longer available for new notifications. |
| process_type | varchar | Defines the processing priority of notification sent using this template. |
| hidden | bool | Indicates whether the template should be hidden in the interface. |
| template_category_id | uuid | Foreign key reference to the category this template belongs to. |
| text_direction_rtl | bool | Indicates whether the template content should be rendered right-to-left. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_templates_history

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for the notification template. |
| name | varchar | Name of the template. |
| template_type | template_type | Categorization of the template (email or sms). |
| created_at | timestamp | Date and time when the template was created. |
| updated_at | timestamp | Date and time when the template was last modified. |
| service_id | uuid | Foreign key reference to the service that owns this template. |
| created_by_id | uuid | Foreign key reference to the user who created the template. |
| version | integer | Version number of the template. |
| archived | bool | Indicates whether the template has been archived and is no longer available for new notifications. |
| process_type | varchar | Defines the processing priority of notification sent using this template. |
| hidden | bool | Indicates whether the template should be hidden in the interface. |
| template_category_id | uuid | Foreign key reference to the category this template belongs to. |
| text_direction_rtl | bool | Indicates whether the template content should be rendered right-to-left. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_notify_user_to_organisation

| Field | Type | Description |
|-------|------|-------------|
| user_id | uuid | Foreign key reference for the user linked to the organisation. |
| organisation_id | uuid | Foreign key reference for the organisation linked to the user. |

### Table: platform_gc_notify_user_to_service

| Field | Type | Description |
|-------|------|-------------|
| user_id | uuid | Foreign key reference for the user linked to the service. |
| service_id | uuid | Foreign key reference for the service linked to the user. |

### Table: platform_gc_notify_users

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Unique identifier for the user account. |
| created_at | timestamp | Date and time when the user account was created. |
| updated_at | timestamp | Date and time when the user account was last modified. |
| password_changed_at | timestamp | Date and time when the user last changed their password. |
| logged_in_at | timestamp | Date and time of the user's most recent successful login. |
| failed_login_count | int4 | Number of consecutive failed login attempts for this user account. |
| state | varchar | Current status of the user account (active, inactive, pending). |
| platform_admin | bool | Indicates whether the user has system-wide administrator privileges. |
| auth_type | varchar | 2FA authentication method used by this user (email_auth, sms_auth). |
| blocked | bool | Indicates whether the user is currently blocked from accessing the system. |
| password_expired | bool | Indicates whether the user's password has expired and needs to be reset. |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |
