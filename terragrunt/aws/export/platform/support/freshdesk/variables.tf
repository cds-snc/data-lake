variable "billing_tag_value" {
  description = "The billing tag value to apply to resources."
  type        = string
}

variable "env" {
  description = "The environment for the resources."
  type        = string
}

variable "freshdesk_api_key" {
  description = "The Freshdesk API key to use for data exports."
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
