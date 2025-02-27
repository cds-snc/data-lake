# Dataset name

A straightforward one or two sentence line explaining what the dataset it. Dataset is one word.

An additional line that describes what each row in the table represents.

If a data pipeline doc exists for this dataset, provide a link to it as well.

`Keywords`: Example, keywords, help, when, searching

## Provenance

Briefly describe where the dataset comes from using words. If from a database, indicate the table or view it is derived from, as well as any critical transformations or filters applied. If the dataset is sourced from a public distribution, link the repo or website where the dataset can be found. If the dataset is collected based on an experiment or survey, link the protocol where analysts can find more details.

* `Updated`: Frequency of update, if automated. If manual, indicate "Manually"
* `Last Updated`: (if manual) Date/time of last time dataset was update
* `Steward`: Who is responsible for the data. This can be a person or an organization.
* `Contact`: Email address or Slack handle of where queries should be directed
* `Location`: (optional) Path to S3 bucket

## Fields

[Link to the first 10-20 rows of the table as CSV](http://www.example.com/dataset.csv). If the head of the table is not representative (e.g., missing data) or sensitive (contains PII), more appropriate rows may be selected instead. Alternatively, a [SQL query](http://www.example.com/dataset.sql) may be provided that returns appropriate example data. This query must be complete, so much that it can be run directly in [Superset's SQL Lab](https://superset.cds-snc.ca/sqllab/) without modification.

A bulleted list of field names must be included, alongside a brief description of the field. Boolean descriptions can simply be the question answered by the boolean. The data type of a field and the unit of measurement should be included as well. The names of data types are dictated by the storage format. For example, the Parquet storage format commonly includes include booleans, dates, floats, integers, strings, times, and timestamps. There is no need to include the integer or float width unless the circumstances are exceptional. 

Sometimes the name of the field is already very descriptive of what the field represents! It's ok if the description adds little value.

For string columns with only a few options (i.e., factors), include what the possible options are.

A few field examples:

| Field Name | Type | Description |
|-------|------|-------------|
| id | string | Version 4 UUID that identifies the user |
| registration_date | datetime | When the user registered, in UTC |
| age | integer | User's age at registration, in years |
| first_name | string | User's first or given name |
| user_hometown | string | User's home town |
| height | float | User's height in centimeters, converted from feet/inches depending on user's localization settings |
| pizza_opinion | string | How much the user indicated they like pizza, one of "Delicious", "It's Alright" or "Hate It". May be missing if user registered before June 20, 2022 |
| first_time_login | boolean | Has the user logged into their account after completing registration? |


## Notes (optional)

Additional details that are relevant to the data set. For example:

"Beginning June 20, 2022, we started asking users how much they liked pizza, and preventing them from logging in if they indicated they hated it".

"We stopped updating this dataset in April 2024 after trying a poutine for the first time and deciding that there was no future for our pizza-based website."