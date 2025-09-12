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
* `Steward`: GC Design System
* `Contact`: Slack channel #ds-cds-internal
* `Location`: `cds-data-lake-transformed-production/platform/gc-design-system/airtable/*/*.json`

## Fields


## Tables & Fields

### 1. `platform_gc_design_system_clients`

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique Airtable record ID |
| created_time | string | Record creation time (ISO 8601) |
| name | string | Hashed client name |
| email | array<string> | Array of hashed email addresses |
| client_status | array<string> | Array of client statuses |
| department | array<string> | Array of department identifiers |
| team | array<string> | Array of team identifiers |
| client_tags | array<string> | Array of tags associated with the client |
| source | array<string> | Array indicating how the client was acquired |
| meetings | array<string> | Array of meeting record IDs |
| date_turned_active_client | string | Date when client became active |
| created | string | Date when client record was created |
| tickets | array<string> | Array of support ticket record IDs |
| date_turned_active_team_from_team | array<string> | Dates when associated team became active |
| crm_id | int | CRM identifier |
| department_name | array<string> | Array of department names |
| notes | string | Additional notes |
| team_tags | array<string> | Array of team tags |
| email_type_from_email | string | Email type information |
| involved_in_engagements | array<string> | Array of engagement activity IDs |

### 2. `platform_gc_design_system_services`

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique Airtable record ID |
| created_time | string | Record creation time (ISO 8601) |
| services | string | Service name |
| link | string | Service link |
| service_status | string | Status of the service |
| teams | array<string> | Array of team identifiers |
| date_of_going_live | string | Date service went live |
| department_from_teams | array<string> | Departments associated via teams |
| departments_autopopulated | array<string> | Autopopulated department names |
| clients_from_teams | array<string> | Clients associated via teams |
| created | string | Date record was created |

### 3. `platform_gc_design_system_teams`

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique Airtable record ID |
| created_time | string | Record creation time (ISO 8601) |
| team_name | string | Team name |
| notes | string | Additional notes |
| use_case | string | Team use case |
| department | array<string> | Array of department identifiers |
| team_tags | array<string> | Array of team tags |
| use_case_tags | array<string> | Array of use case tags |
| clients | array<string> | Array of client identifiers |
| team_status | string | Status of the team |
| date_turned_active_team | string | Date team became active |
| created | string | Date record was created |
| live_service_count | int | Number of live services |
| primary_contact | array<string> | Array of primary contact identifiers |
| summary | string | Team summary |
| date_of_last_meeting | string | Date of last meeting |
| restrictions_to_using_gcds | array<string> | Array of restrictions |
| services | array<string> | Array of service identifiers |

### Example Queries

```sql
-- View sample records from Clients
SELECT * FROM "platform_gc_design_system"."platform_gc_design_system_clients" LIMIT 5;

-- Count total services
SELECT COUNT(*) as total_services FROM "platform_gc_design_system"."platform_gc_design_system_services";

-- List active teams
SELECT team_name, team_status FROM "platform_gc_design_system"."platform_gc_design_system_teams" WHERE team_status = 'Active';

-- Get client engagement by department
SELECT department_name[1] as department, COUNT(*) as client_count
FROM "platform_gc_design_system"."platform_gc_design_system_clients"
GROUP BY department_name[1]
ORDER BY client_count DESC;
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
