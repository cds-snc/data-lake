# Platform / Support / Freshdesk

Dataset providing [Freshdesk](https://www.freshworks.com/freshdesk/) support ticket data raised by the users of CDS products.

Each row is a Freshdesk ticket that does not include any personally identifiable information (PII) or user entered content.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the Physical dataset `platform_support_freshdesk`. 

`Keywords`: Platform, Freshdesk, support, tickets

---

[:information_source:  View the data pipeline](../../../pipelines/platform/support/freshdesk.md)

## Provenance

This dataset is extracted daily using the Freshdesk API.  Each day the extract process downloads all tickets from the previous day that have been updated or created.  These tickets are then merged with the existing tickets in the dataset.

More documentation on the pipeline can be found [here](../../../pipelines/platform/support/freshdesk.md).

* `Updated`: Daily
* `Steward`: Platform Core Services
* `Contact`: [Pat Heard](mailto:patrick.heard@cds-snc.ca)
* `Location`: s3://cds-data-lake-transformed-production/platform/support/freshdesk/month=YYYY-MM/*.parquet

## Fields

Almost all fields are sourced directly from Freshdesk's [Tickets](https://developers.freshdesk.com/api/#tickets), [Contacts](https://developers.freshdesk.com/api/#contacts), and [Conversations](https://developers.freshdesk.com/api/#conversations) API endpoints.

A [query to return example data](examples/freshdesk.sql) has also been provided.

Here's a descriptive list of the Freshdesk ticket fields:

* `id` (integer) - Unique identifier for each support ticket.
* `status` (integer) - Numerical code representing the ticket's current status.
* `status_label` (string) - Human-readable label for the ticket status (e.g., "Open", "Pending", "Resolved").
* `priority` (integer) - Numerical code indicating the ticket's priority level.
* `priority_label` (string) - Human-readable label for the priority level (e.g., "Low", "Medium", "High", "Urgent").
* `source` (integer) - Numerical code indicating how the ticket was created.
* `source_label` (string) - Human-readable label for the ticket source (e.g., "Email", "Phone", "Portal", "Chat").
* `created_at` (timestamp) - Date and time when the ticket was initially created.
* `updated_at` (timestamp) - Date and time of the most recent update to the ticket.
* `due_by` (timestamp) - Deadline for ticket resolution based on support policies.
* `fr_due_by` (timestamp) - First response due time based on support policies.
* `is_escalated` (boolean) - Indicates whether the ticket has been escalated to a higher support tier.
* `tags` (array<string>) - List of labels or categories assigned to the ticket for classification.
* `spam` (boolean) - Indicates whether the ticket has been marked as spam.
* `requester_email_suffix` (string) - Domain portion of the requester's email address.  For non Government of Canada users, this will have the value of `external`.
* `type` (string) - Classification of the ticket type.
* `product_id` (integer) - Unique identifier for the product associated with the ticket.
* `product_name` (string) - Name of the product associated with the ticket.
* `conversations_total_count` (integer) - Total number of messages in the ticket thread.
* `conversations_reply_count` (integer) - Number of replies to and from the user in the ticket thread.
* `conversations_note_count` (integer) - Number of internal notes from the support team added to the ticket.
* `language` (string) - Primary language used in the ticket communication.
* `province_or_territory` (string) - Canadian province or territory where the ticket originated.
* `organization` (string) - Government of Canada department or crown corporation associated with the ticket requester.
* `month` (string) - Month of ticket creation, used as a partition key for data organization.

## Notes

The `language`, `province_or_territory` and `organization` fields are custom fields managed by the Platform Support team.  As such, they will not always have a value populated in the dataset.
