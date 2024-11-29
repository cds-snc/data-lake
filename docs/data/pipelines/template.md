# Dataset name

## Description

A simple description of the dataset explaining what it is. 

If a data catalog doc exists for the pipeline, provide a link to it as well.

## Data pipeline

If possible, provide a high level flow diagram show how the data moves from source system(s) to the data lake.

```mermaid
graph TD
    %% Source Systems
    Source1[Data source name]
    Source2[Data source name]
    
    %% Storage
    RawS3["`**S3 Bucket (Raw)**<br/>cds-data-lake-raw-production`"]
    TransS3["`**S3 Bucket (Transformed)**<br/>cds-data-lake-transformed-production`"]
    
    %% Processing
    Crawlers["Crawlers (frequency)"]
    CatalogRaw["`**Data Catalog (Raw)**<br/>database_name`"]
    CatalogTransformed["`**Data Catalog (Transformed)**<br/>database_name`"]
    ETL["ETL Job (frequency)"]

    %% Flow
    subgraph org[Source system name]
        Source1
        Source2
    end

    Source1 --> |Transfer process|RawS3
    Source2 --> |Transfer process|RawS3

    subgraph datalake[Data Lake account]
        RawS3 --> Crawlers
        Crawlers --> |Updates Schema|CatalogRaw
        CatalogRaw --> ETL
        ETL --> TransS3
        ETL --> CatalogTransformed
    end
```

### Source data

A description of the source data, its origin(s) and owners.

### Crawlers (optional)

Details on how the data's schema is automatically determined.  For some data sources, this will not be required as the data schema will be defined manually.

### Extract, Transform and Load (ETL) Jobs

Provide a description on the ETL jobs, including their:

- source datasets;
- transform steps;
- target datasets; and
- run frequency.
