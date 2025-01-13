output "sns_topic_alarm_action_arn" {
  description = "SNS topic ARN to send alarm actions to"
  value       = aws_sns_topic.cloudwatch_alarm_action.arn
}

output "sns_topic_ok_action_arn" {
  description = "SNS topic ARN to send ok actions to"
  value       = aws_sns_topic.cloudwatch_ok_action.arn
}