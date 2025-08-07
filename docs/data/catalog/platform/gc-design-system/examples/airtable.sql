-- GC Design System Airtable Dataset Example Queries
-- These queries can be run directly in Superset's SQL Lab
-- Note: Column names are normalized (spaces->underscores, no quotes, lowercase)
-- Note: Many fields are arrays, use array[1] to get first element or array functions

-- Basic exploration: View the structure and first few records
SELECT 
    id,
    created_time,
    name,
    client_status[1] as first_client_status  -- Get first element from array
FROM "platform_gc_design_system"."platform_gc_design_system_airtable" 
LIMIT 5;

-- Get schema information
DESCRIBE "platform_gc_design_system"."platform_gc_design_system_airtable";

-- Count total number of clients
SELECT COUNT(*) as total_clients
FROM "platform_gc_design_system"."platform_gc_design_system_airtable";

-- Extract actual fields - working with arrays and strings
SELECT 
    id,
    created_time,
    name as client_name,
    client_status[1] as first_client_status,  -- First element from array
    date_turned_active_client,  -- String field
    created,  -- String field
    department[1] as first_department,  -- First element from array
    team[1] as first_team  -- First element from array
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
LIMIT 10;

-- Group clients by status (using first element of status array)
SELECT 
    client_status[1] as client_status,
    COUNT(*) as client_count
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE cardinality(client_status) > 0  -- Check if array has elements
GROUP BY client_status[1]
ORDER BY client_count DESC;

-- Find active clients
SELECT 
    name as client_name,
    client_status[1] as status,
    date_turned_active_client,
    department[1] as department,
    team[1] as team
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE client_status[1] = 'Active Client (connected)'
ORDER BY date_turned_active_client DESC;

-- Clients with specific tags (checking if array contains value)
SELECT 
    name as client_name,
    client_tags,
    team_tags
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE cardinality(client_tags) > 0  -- Has tags
    AND contains(client_tags, 'GCDS Forum')  -- Contains specific tag
ORDER BY name;

-- Recently created clients (within last 30 days) - note: created_time is string
SELECT 
    id,
    created_time,
    name as client_name,
    created,
    client_status[1] as first_client_status
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE try(date_parse(created_time, '%Y-%m-%dT%H:%i:%s.%fZ')) >= date_add('day', -30, current_timestamp)
ORDER BY created_time DESC;

-- Full text search within client names
SELECT 
    name as client_name,
    client_status[1] as status,
    created,
    email,
    department[1] as first_department
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE lower(name) LIKE '%kortnee%'
ORDER BY name;

-- Count clients by source (using first element of source array)
SELECT 
    source[1] as primary_source,
    COUNT(*) as client_count
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE cardinality(source) > 0
GROUP BY source[1]
ORDER BY client_count DESC;

-- Clients by department and team (using first elements)
SELECT 
    department[1] as primary_department,
    team[1] as primary_team,
    COUNT(*) as client_count
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE cardinality(department) > 0 AND cardinality(team) > 0
GROUP BY department[1], team[1]
ORDER BY client_count DESC;

-- Engagement analysis (working with arrays)
SELECT 
    name as client_name,
    cardinality(involved_in_engagements) as engagement_count,
    involved_in_engagements,
    main_contact_on_engagement,
    themes
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE cardinality(involved_in_engagements) > 0
ORDER BY engagement_count DESC, name;

-- Language preferences (using arrays)
SELECT 
    language_pref[1] as primary_language,
    COUNT(*) as client_count
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE cardinality(language_pref) > 0
GROUP BY language_pref[1]
ORDER BY client_count DESC;

-- Clients with notes
SELECT 
    name as client_name,
    notes,
    client_status[1] as status
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE notes IS NOT NULL AND notes != ''
ORDER BY name;

-- Count total meetings per client
SELECT 
    name as client_name,
    cardinality(meetings) as meeting_count,
    cardinality(tickets) as ticket_count
FROM "platform_gc_design_system"."platform_gc_design_system_airtable"
WHERE cardinality(meetings) > 0 OR cardinality(tickets) > 0
ORDER BY meeting_count DESC, ticket_count DESC;
