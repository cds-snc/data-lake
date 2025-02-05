# BES / CRM / Salesforce

BES stands for Business Enablement Services (a CDS directorate).

CRM stands for Customer Relationship Management.

Dataset providing [CDS Salesforce](https://canadiandigitalservice.my.salesforce.com/) CRM data for CDS products and services.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the Physical dataset `bes_crm_salesforce`.

`Keywords`: Platform, Salesforces, crm, account

---

[:information_source:  View the data pipeline](../../../pipelines/bes/crm/salesforce.md)

## Provenance

This dataset is extracted daily using a Salesforce Python script running in a GitHub workflow.  Each day the extract process downloads most Salesforce tables from the CDS instance and uploads them to an S3 bucket.  These table extracts get overridden every day. 

More documentation on the pipeline can be found [here](../../../pipelines/bes/crm/salesforce.md).

* `Updated`: Daily
* `Steward`: Platform Core Services (pipeline only)
* `Contact`: [Pat Heard](mailto:patrick.heard@cds-snc.ca)
* `Location`: s3://cds-data-lake-transformed-production/bes/crm/salesforce/*.parquet

## Fields

Almost all fields are sourced directly from Salesforce's [tables](https://developers.freshdesk.com/api/#tickets)

A [query to return example data](examples/salesforce.sql) has also been provided.

Here's a descriptive list of the Salesforce account table fields:

* `id` (bigint) - Unique identifier for each account.

## Notes

[Salesforce data analysis](https://docs.google.com/spreadsheets/d/11qiO3HRp-j2pTVBu7X1R-s0XHjRHnX49ClfBNkwgDGk/edit?gid=0#gid=0)