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
