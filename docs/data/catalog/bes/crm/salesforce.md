# BES / CRM / Salesforce

BES stands for Business Enablement Services (a CDS directorate).

CRM stands for Customer Relationship Management.

Dataset providing [CDS Salesforce](https://canadiandigitalservice.my.salesforce.com/) CRM data for CDS products and services.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the Physical dataset `bes_crm_salesforce_production`.

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

Currently, the [ETL script](../../../../../terragrunt/aws/glue/etl/bes/crm/process_salesforce.py) selectively extracts specific fields. This pipeline is a proof of concept demonstrating how Salesforce data can be surfaced through the Platform BI.

A [query to return example data](examples/salesforce.sql) has also been provided.

Here's a descriptive list of the Salesforce `account_opportunity` table fields:

| Field Name               | Type      | Description |
|--------------------------|----------|-------------|
| `accountid`             | string   | Unique identifier for each client account. |
| `accountname`           | string   | Name of the client account. |
| `accountcreateddate`    | timestamp | Date and time when the account was created. |
| `opportunityid`        | string   | Unique identifier for each sales opportunity. |
| `opportunityname`      | string   | Name of the sales opportunity. |
| `opportunitycreateddate` | timestamp | Date and time when the opportunity was created. |
| `product_to_add__c`    | string   | Product associated with the opportunity. |


## Notes

[Salesforce data analysis](https://docs.google.com/spreadsheets/d/11qiO3HRp-j2pTVBu7X1R-s0XHjRHnX49ClfBNkwgDGk/edit?gid=0#gid=0)