variable "cloudwatch_alarm_slack_webhook" {
  description = "Slack webhook URL used by the CloudWatch alarm SNS topics."
  type        = string
  sensitive   = true
}

variable "glue_crawler_log_group_name" {
  description = "The name of the Glue Crawler CloudWatch log group."
  type        = string
}
