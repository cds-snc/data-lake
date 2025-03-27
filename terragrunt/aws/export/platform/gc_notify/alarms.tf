resource "aws_cloudwatch_log_metric_filter" "platform_gc_notify" {
  name           = "${local.gc_notify_lambda_name}-error"
  pattern        = "ERROR"
  log_group_name = "/aws/lambda/${local.gc_notify_lambda_name}"

  metric_transformation {
    name          = "${local.gc_notify_lambda_name}-error"
    namespace     = "data-lake"
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "platform_gc_notify_error_logged" {
  alarm_name          = "${local.gc_notify_lambda_name}-error-logged"
  alarm_description   = "Errors logged over 1 minute by the Platform / GC Notify export."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.platform_gc_notify.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.platform_gc_notify.metric_transformation[0].namespace
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  treat_missing_data  = "notBreaching"

  alarm_actions = [var.sns_topic_alarm_action_arn]
  ok_actions    = [var.sns_topic_ok_action_arn]
}

resource "aws_cloudwatch_metric_alarm" "platform_gc_notify_errors" {
  alarm_name          = "${local.gc_notify_lambda_name}-errors"
  alarm_description   = "Errors metric over 1 minute by the Platform / GC Notify export."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = local.gc_notify_lambda_name
  }

  alarm_actions = [var.sns_topic_alarm_action_arn]
  ok_actions    = [var.sns_topic_ok_action_arn]
}