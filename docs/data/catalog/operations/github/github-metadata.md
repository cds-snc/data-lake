# Operations / GitHub / GitHub Metadata

Dataset describing GitHub activity across CDS repositories including pull requests, commits, and workflow runs.

Each row represents either a pull request, commit, or workflow run from CDS GitHub repositories, providing insights into development activity, code contributions, and CI/CD performance.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as Physical datasets: `operations_github_prs`, `operations_github_commits`, and `operations_github_workflows`.

`Keywords`: GitHub, pull requests, commits, workflows, development, repository, code, version control, CI/CD

---

[:information_source: View the data pipeline](../../../pipelines/operations/github/github-metadata.md)

## Provenance

This dataset is extracted daily from GitHub repositories using the GitHub API. The data is transformed through AWS Glue ETL jobs that explode nested JSON structures into flat, queryable tables. Three separate data sources are processed:
- **Pull Requests (PRs)**: All pull request data from monitored CDS repositories
- **Commit Count**: Git commit history including author, verification status, and commit metadata
- **Workflows**: GitHub Actions workflow run data including status, conclusion, and timing information

More documentation on the pipeline can be found [here](../../../pipelines/operations/github/github-metadata.md).

* `Schedule`: Daily
* `Steward`: Platform Core Services
* `Contact`: Slack channel #platform-core-services

## Fields

The dataset is split into three tables, all derived from GitHub API responses.

### Table 1: Pull Requests (`operations_github_prs`)

Data about pull requests across CDS repositories. Each row represents a single pull request snapshot captured on a specific day when the PR was modified. Since PRs can be updated multiple times, there may be multiple rows for the same PR - use only the most recent row based on the collection date for current PR status.


| Field Name | Type | Description |
|------------|------|-------------|
| metadata_owner | string | GitHub organization owner (e.g., "cds-snc") |
| metadata_repo | string | Repository name where the PR exists |
| id | bigint | Unique GitHub ID for the pull request |
| number | int | Pull request number within the repository |
| title | string | Title of the pull request |
| state | string | Current state of the PR, one of "open", "closed", or "merged" |
| created_at | string | Timestamp when the PR was created (ISO 8601 format) |
| updated_at | string | Timestamp when the PR was last updated (ISO 8601 format) |
| closed_at | string | Timestamp when the PR was closed (ISO 8601 format). May be null if PR is still open |
| html_url | string | Direct URL to the pull request on GitHub |

### Table 2: Commits (`operations_github_commits`)

Data about individual commits across CDS repositories. Each row represents a single commit.


| Field Name | Type | Description |
|------------|------|-------------|
| metadata_owner | string | GitHub organization owner (e.g., "cds-snc") |
| metadata_repo | string | Repository name where the commit exists |
| metadata_time_in_days | int | Number of days in the lookback period for this query |
| metadata_since | string | Start date for the commit query period (ISO 8601 format) |
| author | string | Git author name from the commit |
| date | string | Timestamp when the commit was authored (ISO 8601 format) |
| verified | boolean | Whether the commit signature is verified by GitHub |
| verified_reason | string | Reason for the verification status. Common values include "valid", "unsigned", "unknown_signature_type", "unverified_email" |

### Table 3: Workflows (`operations_github_workflows`)

Data about GitHub Actions workflow runs across CDS repositories. Each row represents a single workflow run.


| Field Name | Type | Description |
|------------|------|-------------|
| metadata_owner | string | GitHub organization owner (e.g., "cds-snc") |
| metadata_repo | string | Repository name where the workflow run occurred |
| id | bigint | Unique GitHub ID for the workflow run |
| name | string | Name of the workflow as defined in the workflow file |
| workflow_id | int | ID of the workflow definition |
| run_number | int | Sequential run number for this workflow within the repository |
| event | string | GitHub event that triggered the workflow (e.g., "push", "pull_request", "schedule") |
| status | string | Current status of the workflow run, one of "queued", "in_progress", "completed" |
| conclusion | string | Final result of the workflow run if completed, one of "success", "failure", "neutral", "cancelled", "skipped", "timed_out", "action_required" |
| created_at | string | Timestamp when the workflow run was created (ISO 8601 format) |
| updated_at | string | Timestamp when the workflow run was last updated (ISO 8601 format) |
| html_url | string | Direct URL to the workflow run on GitHub |

## Notes

**Data Sources**: This dataset combines three separate GitHub API data sources:
1. Pull request metadata for tracking code review and merge activity (captured daily when PRs are modified)
2. Commit history for tracking individual code contributions
3. Workflow runs for tracking CI/CD pipeline performance and outcomes

**Pull Request Data Collection**: Pull requests are collected daily if they were modified on that day. This means the same PR may appear multiple times in the dataset with different snapshots. For current PR status, always use the most recent row for each unique PR (identified by `id` or `metadata_owner`/`metadata_repo`/`number` combination).

**ETL Processing**: The AWS Glue job performs the following transformations:
- Explodes nested JSON arrays into individual rows
- Flattens complex object structures into top-level fields
- Drops intermediate transformation columns (e.g., `metadata_query`)
- Outputs data in Parquet format for efficient querying

**Repository Coverage**: The dataset includes activity from all CDS repositories configured in the GitHub export pipeline. The `metadata_owner` and `metadata_repo` fields identify the specific repository for each row.