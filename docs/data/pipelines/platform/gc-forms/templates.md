# Platform / GC Forms / Templates

### :warning: Note
This dataset is still in testing and only a snapshot of Staging data is available in Superset. 

---

## Description
The GC Forms `Templates` dataset provides information on form templates, and the users that own them, in [Parquet format](https://parquet.apache.org/). The role of the form template is to control how the rendered form is presented to users for submission.

There are no form submissions as part of this dataset and only the form owner's name and Government of Canada email address is available in the `users` table. The data is partitioned by month, and updated daily.  It can be queried in Superset as follows:

Note that this dataset also contains a historical snapshot of published form information that was exported from a manually maintained external source.

```sql
-- Templates
SELECT 
    * 
FROM 
    "platform_gc_forms_production"."platform_gc_forms_template" 
LIMIT 10;

-- Mapping of templates to their owners
SELECT 
    * 
FROM 
    "platform_gc_forms_production"."platform_gc_forms_templatetouser" 
LIMIT 10;

-- Users that have logged into GC Forms
SELECT 
    * 
FROM 
    "platform_gc_forms_production"."platform_gc_forms_user" 
LIMIT 10;

-- Templates with their associated owner user
SELECT 
  template.*,
  user.*
FROM 
  "platform_gc_forms_production.platform_gc_forms_template" AS template
LEFT JOIN
  "platform_gc_forms_production.platform_gc_forms_templatetouser" AS templateToUser
  ON template.id = templateToUser.templateid
LEFT JOIN
  "platform_gc_forms_production.platform_gc_forms_user" AS user
  ON user.id = templateToUser.userid
LIMIT 10;

-- Historical data export
SELECT
    *
FROM
    "platform_gc_forms_production.platform_gc_forms_historical_data"
LIMIT 10;
```

---

[:information_source:  View the data catalog](../../../catalog/platform/gc-forms/templates.md)

## Data pipeline
A high level view is shown below with more details about each step following the diagram.

```mermaid
graph TD
    %% Source Systems
    FormsETL["`**GC Forms ETL**<br/>Database 'Templates' and 'Users' tables`"]
    
    %% Storage
    FormsS3["`**S3 Bucket**<br/>cds-forms-data-lake-bucket-production`"]
    RawS3["`**S3 Bucket (Raw)**<br/>cds-data-lake-raw-production`"]
    TransS3["`**S3 Bucket (Transformed)**<br/>cds-data-lake-transformed-production`"]
    
    %% Processing
    Crawlers["Crawlers (Monthly)"]
    CatalogRaw["`**Data Catalog (Raw)**<br/>platform_gc_forms_production_raw`"]
    CatalogTransformed["`**Data Catalog (Transformed)**<br/>platform_gc_forms_production`"]
    ETL["ETL Job (Daily)"]

    %% Flow
    subgraph org[GC Forms account]
        FormsETL --> FormsS3
    end

    FormsS3 --> |S3 Replication|RawS3

    subgraph datalake[Data Lake account]
        RawS3 --> Crawlers
        Crawlers --> |Updates Schema|CatalogRaw
        CatalogRaw --> ETL
        ETL --> TransS3
        ETL --> CatalogTransformed
    end
```

### Source data
The source of this dataset is the GC Forms database's `Templates` and `Users` tables.  [A nightly ETL job](https://github.com/cds-snc/forms-terraform/blob/main/aws/glue/jobs.tf) runs in the `Forms-Production` AWS account that extracts, transforms and loads data into an S3 bucket.  An [S3 replication rule](https://github.com/cds-snc/forms-terraform/blob/main/aws/glue/s3.tf#L1-L13) then handles moving this data into the Data Lake's Raw bucket.
```
cds-data-lake-raw-production/platform/gc-forms/processed-data/template/*.parquet
cds-data-lake-raw-production/platform/gc-forms/processed-data/templateToUser/*.parquet
cds-data-lake-raw-production/platform/gc-forms/processed-data/user/*.parquet
```

### Crawlers
On the first of each month, an AWS Glue crawler runs in the `DataLake-Production` AWS account to identify schema changes and update the Glue data catalog:

- [Platform / GC Forms / Templates](https://github.com/cds-snc/data-lake/blob/b096d7f2b88aba91a0cb1d8e16985c5b1c42a01a/terragrunt/aws/glue/crawlers.tf#L24-L49)

This crawler creates and manages the following data catalog table in the [`platform_gc_forms_production_raw` database](https://github.com/cds-snc/data-lake/blob/b096d7f2b88aba91a0cb1d8e16985c5b1c42a01a/terragrunt/aws/glue/databases.tf#L6-L9):

- `platform_gc_forms_raw_template`: GC Forms template data.
- `platform_gc_forms_raw_templatetouser`: many-to-many relationship of templates to their owners.
- `platform_gc_forms_raw_user`: GC Forms users that have logged into the service.

### Extract, Transform and Load (ETL) Jobs

Each day, the `Platform / GC Forms / Templates` Glue ETL job runs and updates existing data as well as adding new data.  The resulting dataset is saved in the Data Lake's Transformed `cds-data-lake-transformed-production` S3 bucket:

```
cds-data-lake-transformed-production/platform/gc-forms/processed-data/template/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-forms/processed-data/templateToUser/month=YYYY-MM/*.parquet
cds-data-lake-transformed-production/platform/gc-forms/processed-data/user/month=YYYY-MM/*.parquet
```

Additionally, a data catalog table is created in the [`platform_gc_forms_production` database](https://github.com/cds-snc/data-lake/blob/b096d7f2b88aba91a0cb1d8e16985c5b1c42a01a/terragrunt/aws/glue/databases.tf#L1-L4):

- `platform_gc_forms_template`: deduplicated GC Forms template data.
- `platform_gc_forms_templatetouser`: deduplicated many-to-many relationship of templates to their owners.
- `platform_gc_forms_user`: deduplicated GC Forms users that have logged into the service.
