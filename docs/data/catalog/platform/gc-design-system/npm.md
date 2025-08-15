# Platform / GC Design System / NPM

Dataset providing NPM download statistics for the GC Design System components package.

Each row represents daily download statistics for the `@cdssnc/gcds-components-vue` NPM package, including download counts, dates, and metadata about when the data was collected.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the Physical dataset: `platform_gc_design_system_npm`

`Keywords`: Platform, GC Design System, NPM, Downloads, Statistics, Package Adoption

---

[:information_source: View the data pipeline](../../../pipelines/platform/gc-design-system/npm.md)

## Provenance

This dataset is exported daily from the NPM Registry API, collecting download statistics for the GC Design System Vue components package. The data provides insights into package adoption and usage trends across the Government of Canada ecosystem. More documentation on the pipeline can be found [here](../../../pipelines/platform/gc-design-system/npm.md).

* `Updated`: Daily at 5:00 AM UTC (Production only)
* `Steward`: GC Design System
* `Contact`: Slack channel #ds-cds-internal  
* `Location`: `cds-data-lake-transformed-production/platform/gc-design-system/npm/*.json`

## Fields

All fields are sourced from the NPM Registry API and represent daily download statistics for the GC Design System package.

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| day | string | Download date in YYYY-MM-DD format |
| downloads | bigint | Number of downloads for that specific day |
| package | string | NPM package name (@cdssnc/gcds-components-vue) |
| year | bigint | Year extracted from the download date for partitioning |
| fetched_at | string | Timestamp when data was retrieved from NPM API (ISO 8601 format) |

### Example Queries

```sql
-- View recent download trends
SELECT day, downloads
FROM "platform_gc_design_system"."platform_gc_design_system_npm"
WHERE year = 2024
ORDER BY day DESC
LIMIT 30;

-- Monthly download aggregations
SELECT 
  DATE_TRUNC('month', CAST(day AS DATE)) as month,
  SUM(downloads) as total_downloads,
  AVG(downloads) as avg_daily_downloads,
  MAX(downloads) as peak_daily_downloads
FROM "platform_gc_design_system"."platform_gc_design_system_npm"
GROUP BY DATE_TRUNC('month', CAST(day AS DATE))
ORDER BY month DESC;

-- Year-over-year growth analysis
SELECT 
  year,
  SUM(downloads) as yearly_downloads,
  LAG(SUM(downloads)) OVER (ORDER BY year) as previous_year,
  ROUND(
    (SUM(downloads) - LAG(SUM(downloads)) OVER (ORDER BY year)) * 100.0 / 
    LAG(SUM(downloads)) OVER (ORDER BY year), 2
  ) as growth_percentage
FROM "platform_gc_design_system"."platform_gc_design_system_npm"
GROUP BY year
ORDER BY year;

-- Get total downloads and data range
SELECT 
  COUNT(*) as total_days,
  SUM(downloads) as total_downloads,
  MIN(day) as earliest_date,
  MAX(day) as latest_date,
  MAX(fetched_at) as last_updated
FROM "platform_gc_design_system"."platform_gc_design_system_npm";
```

## Notes

- **Data Quality**: Data is fetched daily but represents complete historical data from NPM. Missing days may indicate no downloads or temporary API issues.
- **Package Scope**: Currently tracks only the Vue components package (`@cdssnc/gcds-components-vue`). Additional packages may be added in future iterations.
- **Usage Tracking**: This data complements other GC Design System analytics including [Airtable client engagement data](./airtable.md) for a complete adoption picture.
