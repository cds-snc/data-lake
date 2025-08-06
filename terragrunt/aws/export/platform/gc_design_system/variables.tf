variable "billing_tag_value" {
  description = "The billing tag value to apply to resources."
  type        = string
}

variable "airtable_api_key" {
  description = "Airtable API key for accessing the design system base"
  type        = string
  sensitive   = true
}

variable "env" {
  description = "The environment for the resources."
  type        = string
}

variable "transformed_bucket_arn" {
  description = "The ARN of the transformed bucket"
  type        = string
}

variable "transformed_bucket_name" {
  description = "The name of the transformed bucket"
  type        = string
}

variable "raw_bucket_arn" {
  description = "The ARN of the raw bucket"
  type        = string
}

variable "raw_bucket_name" {
  description = "The name of the raw bucket"
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
