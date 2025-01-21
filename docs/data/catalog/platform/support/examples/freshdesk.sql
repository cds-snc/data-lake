/*
This query will return the first ten rows of the "Freshdesk"
dataset. To run it, open the SQL Lab in Superset and cut and paste the whole
query into the query window.

SQL Lab: https://superset.cds-snc.ca/sqllab/

The example dataset is provided as a query instead of a CSV to limit
visibility to only those with Superset access.
*/

SELECT
  *
FROM
  platform_support_production.platform_support_freshdesk 
LIMIT 10;
