# Operations / GitHub / Metadata Alerts

Dataset describing security alerts across CDS repositories including Dependabot alerts and code scanning alerts.

Each row represents either a Dependabot vulnerability alert or a code scanning alert from CDS GitHub repositories, providing insights into security vulnerabilities, dependencies, and code quality issues.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as Physical datasets: `operations_github_dependabot` and `operations_github_code_scanning_alerts`.

`Keywords`: GitHub, security, Dependabot, code scanning, vulnerabilities, dependencies, SAST, code analysis

---

[:information_source: View the data pipeline](../../../pipelines/operations/github/github-metadata-alerts.md)

## Provenance

This dataset is extracted daily from GitHub repositories using the GitHub API. The data is transformed through AWS Glue ETL jobs that explode nested JSON structures into flat, queryable tables. Two separate data sources are processed:
- **Dependabot Alerts**: Vulnerability alerts for dependencies in monitored CDS repositories
- **Code Scanning Alerts**: Security and quality issues detected by code scanning analysis

More documentation on the pipeline can be found [here](../../../pipelines/operations/github/github-metadata-alerts.md).

* `Schedule`: Daily
* `Steward`: Platform Core Services
* `Contact`: Slack channel #platform-core-services

## Fields

The dataset is split into two tables, both derived from GitHub API responses.

### Table 1: Dependabot Alerts (`operations_github_dependabot`)

Data about Dependabot vulnerability alerts across CDS repositories. Each row represents a single vulnerability alert for a dependency. Multiple alerts can exist for the same repository and severity.

| Field Name | Type | Description |
|------------|------|-------------|
| metadata_owner | string | GitHub organization owner (e.g., "cds-snc") |
| metadata_repo | string | Repository name where the alert exists |
| n_alerts | int | Total number of Dependabot alerts for this repository |
| cvss_vector_string | string | CVSS vector string describing the vulnerability scoring |
| cvss_score_int | int | CVSS integer score component |
| cvss_score_double | double | CVSS decimal score component |
| created_at | string | Timestamp when the alert was created (ISO 8601 format) |
| ghsa_id | string | GitHub Security Advisory ID (e.g., "GHSA-xxxx-xxxx-xxxx") |
| severity | string | Severity level of the vulnerability, one of "critical", "high", "medium", "low" |
| dependency_manifest_path | string | Path to the dependency manifest file (e.g., package.json, requirements.txt) |
| dependency_scope | string | Scope of the dependency, one of "runtime", "development" |
| dependency_package_name | string | Name of the vulnerable package |
| dependency_package_ecosystem | string | Ecosystem of the package (e.g., "npm", "pip", "maven", "nuget") |
| dependency_relationship | string | Relationship type of the dependency |
| cve_id | string | CVE ID for the vulnerability if available |
| alert_cwes | array<struct> | Array of CWE (Common Weakness Enumeration) objects associated with the vulnerability |
| cwes_cwe_id | string | CWE ID (e.g., "CWE-123") |
| cwes_name | string | Name of the CWE weakness |
| alert_id | int | Unique GitHub ID for this alert |

### Table 2: Code Scanning Alerts (`operations_github_code_scanning_alerts`)

Data about code scanning alerts across CDS repositories. Each row represents a single code scanning alert discovery.

| Field Name | Type | Description |
|------------|------|-------------|
| metadata_owner | string | GitHub organization owner (e.g., "cds-snc") |
| metadata_repo | string | Repository name where the alert exists |
| number | int | Alert number within the repository |
| created_at | string | Timestamp when the alert was created (ISO 8601 format) |
| updated_at | string | Timestamp when the alert was last updated (ISO 8601 format) |
| url | string | API URL for the alert |
| html_url | string | Direct URL to the alert on GitHub |
| state | string | Current state of the alert, one of "open", "dismissed", "fixed" |
| fixed_at | string | Timestamp when the alert was fixed (null if not fixed) |
| dismissed_by | string | GitHub username of the user who dismissed the alert (null if not dismissed) |
| dismissed_at | string | Timestamp when the alert was dismissed (null if not dismissed) |
| dismissed_reason | string | Reason for dismissal (null if not dismissed) |
| dismissed_comment | string | Comment on the dismissal (null if not dismissed) |
| rule.id | string | Unique identifier for the analysis rule that generated this alert |
| rule.severity | string | Severity level determined by the rule, one of "error", "warning", "note" |
| rule.description | string | Human-readable description of the rule |
| rule.name | string | Name of the rule |
| rule.full_description | string | Full technical description of the rule |
| rule.security_severity_level | string | Security severity level, one of "critical", "high", "medium", "low", "note" |
| tool.name | string | Name of the code scanning tool (e.g., "CodeQL", "Semgrep") |
| tool.version | string | Version of the scanning tool used |
| most_recent_instance.ref | string | Git reference (branch or commit SHA) where the alert was detected |
| most_recent_instance.analysis_key | string | Unique key for the analysis |
| most_recent_instance.environment | string | Environment where the alert was detected |
| most_recent_instance.category | string | Category of the alert |
| most_recent_instance.state | string | State of the alert instance |
| most_recent_instance.commit_sha | string | Git commit SHA where the issue was found |
| most_recent_instance.message.text | string | Message describing the alert instance |
| most_recent_instance.location.path | string | File path where the issue was detected |
| most_recent_instance.location.start_line | int | Starting line number of the issue in the file |
| most_recent_instance.location.end_line | int | Ending line number of the issue in the file |
| most_recent_instance.location.start_column | int | Starting column number of the issue |
| most_recent_instance.location.end_column | int | Ending column number of the issue |
| instances_url | string | URL to view all instances of this alert |

## Notes

**Data Sources**: This dataset combines two separate GitHub API data sources:
1. Dependabot vulnerability alerts providing dependency security information
2. Code scanning alerts providing static analysis security and quality findings

**Alert States**: Both alert types track their lifecycle through state changes:
- Dependabot alerts can be open or resolved
- Code scanning alerts track open, dismissed, and fixed states

**ETL Processing**: The AWS Glue job performs the following transformations:
- Explodes nested JSON arrays into individual rows for each alert
- Flattens complex object structures into top-level fields
- Separates Dependabot alerts and code scanning alerts into distinct tables
- Drops intermediate transformation columns (e.g., `metadata_query`)
- Outputs data in Parquet format for efficient querying

**Repository Coverage**: The dataset includes security alerts from all CDS repositories configured in the GitHub export pipeline. The `metadata_owner` and `metadata_repo` fields identify the specific repository for each row.

**Data Freshness**: Alerts are collected daily and represent the current state of security issues in the repository. Historical tracking of alert state changes is maintained through the `created_at`, `updated_at`, and dismissal timestamps.
