resource "aws_cloudwatch_log_metric_filter" "platform_support_freshdesk_export" {
  name           = "platform-support-freshdesk-export-error"
  pattern        = "ERROR"
  log_group_name = "/aws/lambda/${module.platform_support_freshdesk_export.function_name}"

  metric_transformation {
    name          = "platform-support-freshdesk-export-error"
    namespace     = "data-lake"
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "platform_support_freshdesk_export" {
  alarm_name          = "platform-support-freshdesk-export-error"
  alarm_description   = "Errors logged over 1 minute by the Platform / Support / Freshdesk export."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.platform_support_freshdesk_export.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.platform_support_freshdesk_export.metric_transformation[0].namespace
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  treat_missing_data  = "notBreaching"

  alarm_actions = [var.sns_topic_alarm_action_arn]
  ok_actions    = [var.sns_topic_ok_action_arn]
}
