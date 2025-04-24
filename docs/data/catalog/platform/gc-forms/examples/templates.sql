/*
This query will return the first ten rows of each table in the dataset. 
To run it, open the SQL Lab in Superset and cut and paste the whole
query into the query window.

SQL Lab: https://superset.cds-snc.ca/sqllab/

The example dataset is provided as a query instead of a CSV to limit
visibility to only those with Superset access.
*/

-- Submissions
SELECT 
    * 
FROM 
    "platform_gc_forms_production"."platform_gc_forms_submissions" 
LIMIT 10;

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
  platform_gc_forms_production.platform_gc_forms_template AS template
LEFT JOIN
  platform_gc_forms_production.platform_gc_forms_templatetouser AS templateToUser
  ON template.id = templateToUser.templateid
LEFT JOIN
  platform_gc_forms_production.platform_gc_forms_user AS user
  ON user.id = templateToUser.userid
LIMIT 10;