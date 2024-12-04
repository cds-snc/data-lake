/*
This query will return the first ten rows of the "AWS Cost and Usage Report"
dataset. To run it, open the SQL Lab in Superset and cut and paste the whole
query into the query window.

SQL Lab: https://superset.cdssandbox.xyz/sqllab/

The example dataset is provided as a query instead of a CSV to limit
visibility to only those with Superset access.
*/

SELECT
  *
FROM
  operations_aws_production.cost_usage_report_by_account 
LIMIT 10;