variable "account_id" {
  description = "The AWS account ID"
  type        = string
}

variable "billing_tag_value" {
  description = "The billing tag value to apply to resources."
  type        = string
}

variable "raw_bucket_name" {
  description = "The name of the Raw bucket"
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
