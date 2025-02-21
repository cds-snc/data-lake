# Platform / GC Forms / Templates

### :warning: Note
This dataset is still in testing and only a snapshot of Staging data is available in Superset. 

---

Dataset providing GC Forms template data.  There are 3 tables as part of this dataset:

- `template`: the templates that are used by GC Forms to render the form users fill out and submit.
- `templateToUser`: a many-to-many relationship of templates to their owners.
- `user`: the users that have logged into GC Forms.

No external user form submissions are part of this dataset. The only personally identifiable information (PII) is the user name and Government of Canada email address.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the following Physical datasets:

- `platform_gc_forms_template` 
- `platform_gc_forms_templatetouser`
- `platform_gc_forms_user`

`Keywords`: Platform, GC Forms, templates

---

[:information_source:  View the data pipeline](../../../pipelines/platform/gc-forms/templates.md)

## Provenance

This dataset is extracted daily from the GC Forms database's `Templates` and `Users` tables. More documentation on the pipeline can be found [here](../../../pipelines/platform/gc-forms/templates.md).

* `Updated`: Daily
* `Steward`: GC Forms and Platform Core Services
* `Contact`: [Vivian Nobrega](mailto:vivian.nobrega@cds-snc.ca) and [Pat Heard](mailto:patrick.heard@cds-snc.ca)
* `Location`: 
```
s3://cds-data-lake-transformed-production/platform/gc-forms/processed-data/template/month=YYYY-MM/*.parquet
s3://cds-data-lake-transformed-production/platform/gc-forms/processed-data/templateToUser/month=YYYY-MM/*.parquet
s3://cds-data-lake-transformed-production/platform/gc-forms/processed-data/user/month=YYYY-MM/*.parquet
```

## Fields

Almost all fields are sourced directly from the GC Forms database's `Templates` and `Users` table.

[Queries to return example data](examples/templates.sql) have also been provided.

Here's a descriptive list of the fields in each table:

### Table: platform_gc_forms_template

* `id` (varchar) - unique identifier for the template
* `ttl` (timestamp) - time-to-live timestamp, after which the template will be removed.
* `ispublished` (boolean) - indicates whether the template has been published.
* `created_at` (timestamp) - date the template was created.
* `updated_at` (timestamp) - date the template was last updated.
* `name` (varchar) - name of the template.
* `securityattribute` (varchar) - security classification of data collected by the template: [Protected A, Protected B, Unclassified].
* `closingdate` (timestamp) - when the template was closed, or null if still open.
* `formpurpose` (varchar) - purpose of the template: [Administrative,  Non-Administrative].
* `publishdesc` (varchar) - reason for publishing the template, as described by the user.
* `publishformtype` (varchar) - type of published template: [Collection of Feedback or Stats, Benefit Administration, Grants and Contributions, Regulatory Compliance, Organizational Operations, Other].
* `publishreason` (varchar) - reason for publishing: [Ready for public use, Ready for internal use, Sharing for feedback or approval, Other].
* `closeddetails` (varchar) - reason for closing the template to submissions.
* `deliveryemaildestination` (varchar) - email destination for submission delivery, null if email delivery not enabled.
* `api_created_at` (timestamp) - when API integration was enabled for the template, null if no API integration.
* `api_id` (varchar) - API identifier, null if no API integration.
* `deliveryoption` (integer) - template submission delivery method: [0 = Download, 1 = Email, 2 = API, 99 = Error].
* `timestamp` (timestamp) - time of the last extract of the template record.
* `titleen` (varchar) - template title in English.
* `titlefr` (varchar) - template title in French.
* `brand` (varchar) - branding used by the template.
* `addresscomplete_count` (bigint) - count of address complete elements.
* `checkbox_count` (bigint) - count of checkbox form elements.
* `combobox_count` (bigint) - count of combobox form elements.
* `dropdown_count` (bigint) - count of dropdown form elements.
* `dynamicrow_count` (bigint) - count of dynamic row form elements.
* `fileinput_count` (bigint) - count of file input form elements.
* `formatteddate_count` (bigint) - count of formatted date elements.
* `radio_count` (bigint) - count of radio button form elements.
* `richtext_count` (bigint) - count of rich text form elements.
* `textarea_count` (bigint) - count of textarea form elements.
* `textfield_count` (bigint) - count of text field form elements.
* `saveandresume` (boolean) - indicates if template allows save and resume functionality.
* `month` (varchar) - partition key in the format of YYYY-MM.
			
### Table: platform_gc_forms_templatetouser

* `templateid` (varchar) - template ID of the relationship.
* `userid` (varchar) - user ID of the relationship.
* `timestamp` (timestamp) - time of the last extract of the relationship record.
				
### Table: platform_gc_forms_user		

* `id` (varchar) - unique identifier for the user.
* `name` (varchar) - user's full name.
* `email` (varchar) - user's Government of Canada email address.
* `emailverified` (timestamp) - when the user's email was verified.
* `lastlogin` (timestamp) - time of user's most recent login.
* `active` (boolean) - indicates whether the user account is active.
* `createdat` (timestamp) - when the user account was created.
* `notes` (varchar) - additional notes about the user.
* `timestamp` (timestamp) - time of the last extract of the user record.
* `month` (varchar) - partition key in the format of YYYY-MM.
