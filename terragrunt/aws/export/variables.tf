variable "freshdesk_api_key" {
  description = "The Freshdesk API key to use for data exports."
  type        = string
  sensitive   = true
}

variable "airtable_api_key" {
  description = "Airtable API key for accessing the design system base"
  type        = string
  sensitive   = true
}

variable "airtable_base_id" {
  description = "Airtable base ID for the GC Design System base"
  type        = string
  sensitive   = true
}

variable "airtable_table_name_clients" {
  description = "Airtable table name for the GC Design System clients data"
  type        = string
  sensitive   = true
}

variable "airtable_table_name_teams" {
  description = "Airtable table name for the GC Design System teams data"
  type        = string
  sensitive   = true
}

variable "airtable_table_name_services" {
  description = "Airtable table name for the GC Design System services data"
  type        = string
  sensitive   = true
}

variable "raw_bucket_arn" {
  description = "The ARN of the Raw bucket."
  type        = string
}

variable "raw_bucket_name" {
  description = "The name of the Raw bucket."
  type        = string
}

variable "sns_topic_alarm_action_arn" {
  description = "The ARN of the SNS topic to send alarm actions to."
  type        = string
}

variable "sns_topic_ok_action_arn" {
  description = "The ARN of the SNS topic to send OK actions to."
  type        = string
}

variable "transformed_bucket_arn" {
  description = "The ARN of the Transformed bucket"
  type        = string
}

variable "transformed_bucket_name" {
  description = "The name of the Transformed bucket"
  type        = string
}

variable "gc_design_system_crawler_arn" {
  description = "The ARN of the GC Design System Glue crawler"
  type        = string
}

variable "gc_design_system_crawler_name" {
  description = "The name of the GC Design System Glue crawler"
  type        = string
}

variable "gc_design_system_npm_crawler_arn" {
  description = "The ARN of the GC Design System NPM Glue crawler"
  type        = string
}

variable "gc_design_system_npm_crawler_name" {
  description = "The name of the GC Design System NPM Glue crawler"
  type        = string
}
