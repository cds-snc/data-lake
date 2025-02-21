/*
This query will return the first ten rows of each table in the dataset. 
To run it, open the SQL Lab in Superset and cut and paste the whole
query into the query window.

SQL Lab: https://superset.cds-snc.ca/sqllab/

The example dataset is provided as a query instead of a CSV to limit
visibility to only those with Superset access.
*/

-- Forms users that have created a template
SELECT 
    * 
FROM 
    "platform_gc_forms_production"."platform_gc_forms_user" 
LIMIT 10;

-- Forms templates
SELECT 
    * 
FROM 
    "platform_gc_forms_production"."platform_gc_forms_template" 
LIMIT 10;

-- Mapping of users to their templates
SELECT 
    * 
FROM 
    "platform_gc_forms_production"."platform_gc_forms_templatetouser" 
LIMIT 10;
