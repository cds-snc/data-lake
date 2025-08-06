# Platform / GC Design System / Airtable

Dataset providing GC Design System client and engagement data exported from Airtable.

Each row represents a client or user of the Government of Canada Design System, including their contact information, engagement status, team associations, meeting history, and support interactions.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the Physical dataset: `platform_gc_design_system_airtable`

`Keywords`: Platform, GC Design System, Airtable, Clients, Engagement, Support

---

[:information_source: View the data pipeline](../../../pipelines/platform/gc-design-system/airtable.md)

## Provenance

This dataset is exported daily from the GC Design System Airtable base using the Airtable API. The data contains client engagement information, support interactions, and relationship data for users and organizations working with the Government of Canada Design System. More documentation on the pipeline can be found [here](../../../pipelines/platform/gc-design-system/airtable.md).

* `Updated`: Daily at 5:00 AM UTC (Production only)
* `Steward`: Platform Core Services
* `Contact`: Slack channel #platform-core-services
* `Location`: `cds-data-lake-transformed-production/platform/gc-design-system/airtable/*.jsonl`

## Fields

All fields are sourced directly from the GC Design System Airtable base. The exact schema is automatically discovered and may evolve as the Airtable structure changes.

[Query to return example data](examples/airtable.sql) has been provided to explore the current structure.

Here's a descriptive list of the core fields that are typically present:

### Core Airtable Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique record identifier assigned by Airtable (format: recXXXXXXXXXXXXXX) |
| created_time | timestamp | When the record was created in Airtable, in ISO 8601 format (UTC) |

### Actual Fields in the Dataset

*Note: The Lambda function normalizes column names by replacing spaces with underscores, removing quotes and parentheses, and converting to lowercase. Many fields are arrays since Airtable often stores linked records and multi-select fields as arrays:*

| Field | Type | Description |
|-------|------|-------------|
| name | string | Client's full name |
| email | array<string> | Array of email addresses (Airtable linked records) |
| client_status | array<string> | Array of client statuses (e.g., ["Active Client (connected)"]) |
| department | array<string> | Array of department or organization identifiers (Airtable linked records) |
| team | array<string> | Array of team identifiers (Airtable linked records) |
| client_tags | array<string> | Array of tags associated with the client (e.g., ["Mailing List", "GCDS Forum"]) |
| source | array<string> | Array indicating how the client was acquired (e.g., ["Support Ticket"]) |
| meetings | array<string> | Array of meeting record identifiers (Airtable linked records) |
| date_turned_active_client | string | Date when client became active (stored as string, format varies) |
| created | string | Date when the client record was created (stored as string, format varies) |
| tickets | array<string> | Array of support ticket record identifiers (Airtable linked records) |
| date_turned_active_team_from_team | array<string> | Array of dates when associated team became active |
| notes | string | Additional notes about the client |
| team_tags | array<string> | Array of tags associated with the client's team |
| involved_in_engagements | array<string> | Array of engagement activity identifiers |
| primary_contact_on_team | array<string> | Array of primary contact identifiers for the team |
| non_team_use_case | string | Use cases outside of team context |
| main_contact_on_meetings | array<string> | Array of primary contact identifiers for meeting coordination |
| themes | array<string> | Array of themes or topics associated with the client |
| language_pref | array<string> | Array of client's preferred languages |
| contributions | array<string> | Array of contribution identifiers made by the client |
| main_contact_on_engagement | array<string> | Array of primary contact identifiers for engagement activities |

### Example Queries

To explore the current data structure:

```sql
-- View sample records to understand current structure
SELECT * 
FROM "platform_gc_design_system"."platform_gc_design_system_airtable" 
LIMIT 5;

-- Get table schema information
DESCRIBE "platform_gc_design_system"."platform_gc_design_system_airtable";

-- Count total clients
SELECT COUNT(*) as total_clients
FROM "platform_gc_design_system"."platform_gc_design_system_airtable";

-- View client information (working with arrays)
SELECT 
    id,
    name as client_name,
    client_status[1] as first_client_status,  -- Get first element from array
    date_turned_active_client,  -- String field
    department[1] as first_department,  -- Get first element from array
    team[1] as first_team  -- Get first element from array
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
LIMIT 10;
```

## Notes

- **Dynamic Schema**: The schema of this dataset is automatically discovered by AWS Glue crawlers and will change as the Airtable structure evolves. Always check the current schema using `DESCRIBE` queries before writing production queries.

- **Normalized Column Names**: The Lambda function automatically normalizes column names by replacing spaces with underscores, removing quotes and parentheses, and converting to lowercase. This makes querying much easier and eliminates the need for quoted column names.

- **Array Fields**: Most fields are arrays since Airtable stores linked records and multi-select fields as arrays. Use `field[1]` to get the first element, `cardinality(field)` to check array size, and `contains(field, 'value')` to check if array contains a specific value.

- **String Dates**: Date fields like `created_time`, `date_turned_active_client`, and `created` are stored as strings, not date types. Use `date_parse()` or `try(date_parse())` functions when you need to work with them as dates.

- **Flattened Structure**: Data is stored in JSONL format but the Glue crawler flattens the structure, making all fields accessible as top-level columns. No JSON extraction functions needed!

- **Field Availability**: Not all records may contain all fields, as Airtable allows sparse data. Always check for NULL values or empty arrays when querying specific fields.

- **Airtable Limitations**: The data reflects the current state of the Airtable base and does not include historical versions of records (unless specifically tracked within Airtable).

- **Data Freshness**: Data is refreshed daily. For real-time data, query the Airtable API directly (requires separate authentication).

- **Character Encoding**: All text fields support Unicode characters and may contain rich text formatting depending on how they're configured in Airtable.
