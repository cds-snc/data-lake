# Platform / GC Forms / Templates

Dataset providing GC Forms template data.  There are five tables as part of this dataset:

- `historical_data`: one-time snapshot of published form data that was previously managed in an external source.
- `submissions`: one-to-many relationship of templates to their submission IDs (no user submitted data).
- `template`: the templates that are used by GC Forms to render the form users fill out and submit.
- `templateToUser`: a many-to-many relationship of templates to their owners.
- `user`: the users that have logged into GC Forms.

No external user form submissions or personally identifiable information (PII) are part of this dataset.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the following Physical datasets:

- `platform_gc_forms_historical_data`
- `platform_gc_forms_submissions` 
- `platform_gc_forms_template` 
- `platform_gc_forms_templatetouser`
- `platform_gc_forms_user`

## :warning: Note
This is a time series dataset.  Each day, an entirely new extract of all Forms data is added.  To retrieve only the latest extract's data, use the `timestamp` field of the tables:

```sql
SELECT *
FROM "platform_gc_forms_production"."platform_gc_forms_template"
WHERE timestamp =
    (SELECT MAX(timestamp)
     FROM "platform_gc_forms_production"."platform_gc_forms_template");
```

`Keywords`: Platform, GC Forms, templates

---

[:information_source:  View the data pipeline](../../../pipelines/platform/gc-forms/templates.md)

## Provenance

With the exception of the `historical_data`, this dataset is extracted daily from the GC Forms database's `Templates` and `Users` tables. More documentation on the pipeline can be found [here](../../../pipelines/platform/gc-forms/templates.md).

* `Updated`: Daily
* `Steward`: GC Forms
* `Contact`: [Vivian Nobrega](mailto:vivian.nobrega@cds-snc.ca)
* `Location`: 
```
s3://cds-data-lake-transformed-production/platform/gc-forms/historical-data/month=YYYY-MM/*.parquet
s3://cds-data-lake-transformed-production/platform/gc-forms/processed-data/submissions/month=YYYY-MM/*.parquet
s3://cds-data-lake-transformed-production/platform/gc-forms/processed-data/template/month=YYYY-MM/*.parquet
s3://cds-data-lake-transformed-production/platform/gc-forms/processed-data/templateToUser/month=YYYY-MM/*.parquet
s3://cds-data-lake-transformed-production/platform/gc-forms/processed-data/user/month=YYYY-MM/*.parquet
```

## Fields

Almost all fields are sourced directly from the GC Forms database's `Templates` and `Users` table.

[Queries to return example data](examples/templates.sql) have also been provided.

Here's a descriptive list of the fields in each table:

### Table: platform_gc_forms_historical_data

| Field | Type | Description |
|-------|------|-------------|
| unique_id | string | Unique identifier for the historical record |
| date | timestamp | Timestamp when the historical record was created |
| metric | string | Type of historical record |
| metric_format__from_metric_ | string | Format of the metric field (always "Number") |
| unit_of_measurement | string | Unit used for measuring the metric |
| department | string | Government department associated with the form |
| client_email | string | Email address domain of the client who owns the form |
| number_value | string | Numerical value of the metric (always "1") |
| security_classification | string | Security classification of the form data (Protected A, Protected B, Unclassified) |
| comment | string | Additional comments about the record |
| publishing_description | string | Description provided when publishing the form |
| published_form_type | string | Type of published form (Collection of Feedback, Benefit Administration, etc.) |
| published_reason | string | Reason for publishing the form |
| recorded_by | string | User who recorded this historical data entry |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |

### Table: platform_gc_forms_submissions

| Field | Type | Description |
|-------|------|-------------|
| submission_id | string | Submission ID of the relationship |
| form_id | string | Template ID of the relationship |
| timestamp | timestamp | Time of the last extract of the relationship record |

### Table: platform_gc_forms_template

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the template |
| ttl | timestamp | Time-to-live timestamp, after which the template will be removed |
| ispublished | boolean | Indicates whether the template has been published |
| created_at | timestamp | Date the template was created |
| updated_at | timestamp | Date the template was last updated |
| name | string | Name of the template |
| securityattribute | string | Security classification of data collected by the template: [Protected A, Protected B, Unclassified] |
| closingdate | timestamp | When the template was closed, or null if still open |
| formpurpose | string | Purpose of the template: [Administrative, Non-Administrative] |
| publishdesc | string | Reason for publishing the template, as described by the user |
| publishformtype | string | Type of published template: [Collection of Feedback or Stats, Benefit Administration, Grants and Contributions, Regulatory Compliance, Organizational Operations, Other] |
| publishreason | string | Reason for publishing: [Ready for public use, Ready for internal use, Sharing for feedback or approval, Other] |
| closeddetails | string | Reason for closing the template to submissions |
| deliveryemaildestination | string | Email domain from the delivery destination email address, or null if email delivery is not enabled |
| api_created_at | timestamp | When API integration was enabled for the template, null if no API integration |
| api_id | string | API identifier, null if no API integration |
| deliveryoption | integer | Template submission delivery method: [0 = Download, 1 = Email, 2 = API, 99 = Error] |
| timestamp | timestamp | Time of the last extract of the template record |
| titleen | string | Template title in English |
| titlefr | string | Template title in French |
| brand | string | Branding used by the template |
| addresscomplete_count | integer | Count of address complete elements |
| checkbox_count | integer | Count of checkbox form elements |
| combobox_count | integer | Count of combobox form elements |
| dropdown_count | integer | Count of dropdown form elements |
| dynamicrow_count | integer | Count of dynamic row form elements |
| fileinput_count | integer | Count of file input form elements |
| formatteddate_count | integer | Count of formatted date elements |
| radio_count | integer | Count of radio button form elements |
| richtext_count | integer | Count of rich text form elements |
| textarea_count | integer | Count of textarea form elements |
| textfield_count | integer | Count of text field form elements |
| saveandresume | boolean | Indicates if template allows save and resume functionality |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |
			
### Table: platform_gc_forms_templatetouser

| Field | Type | Description |
|-------|------|-------------|
| templateid | string | Template ID of the relationship |
| userid | string | User ID of the relationship |
| timestamp | timestamp | Time of the last extract of the relationship record |
				
### Table: platform_gc_forms_user		

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the user |
| email | string | User's Government of Canada email address domain |
| emailverified | timestamp | When the user's email was verified |
| lastlogin | timestamp | Time of user's most recent login |
| active | boolean | Indicates whether the user account is active |
| createdat | timestamp | When the user account was created |
| notes | string | Additional notes about the user |
| canpublish | boolean | Indicates if the user can publish forms |
| timestamp | timestamp | Time of the last extract of the user record |
| year | string | Partition key in the format of YYYY |
| month | string | Partition key in the format of YYYY-MM |
