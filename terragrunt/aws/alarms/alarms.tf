#
# Glue Crawler errors
#
resource "aws_cloudwatch_log_metric_filter" "glue_crawler_error" {
  name           = "glue-crawler-error"
  pattern        = local.glue_crawler_metric_filter_error_pattern
  log_group_name = var.glue_crawler_log_group_name

  metric_transformation {
    name          = local.glue_crawler_error_metric_name
    namespace     = local.data_lake_namespace
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "glue_crawler_error" {
  alarm_name          = "glue-crawler-error"
  alarm_description   = "Errors logged over 1 minute by the Glue Crawler."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.glue_crawler_error.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.glue_crawler_error.metric_transformation[0].namespace
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.cloudwatch_alarm_action.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_ok_action.arn]
}

#
# Log Insight queries
#
resource "aws_cloudwatch_query_definition" "glue_crawler_errors" {
  name = "Glue Crawler - ERRORS"

  log_group_names = [var.glue_crawler_log_group_name]

  query_string = <<-QUERY
    fields @timestamp, @message, @logStream
    | filter @message like /${local.glue_crawler_metric_filter_error_pattern}/
    | sort @timestamp desc
    | limit 100
  QUERY
}