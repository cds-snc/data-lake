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
# Glue ETL errors
#
resource "aws_cloudwatch_log_metric_filter" "glue_etl_pythonshell_error" {
  name           = "glue-etl-pythonshell-error"
  pattern        = local.glue_etl_pythonshell_metric_filter_error_pattern
  log_group_name = "${var.glue_etl_pythonshell_log_group_name}/error"

  metric_transformation {
    name          = local.glue_etl_pythonshell_error_metric_name
    namespace     = local.data_lake_namespace
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "glue_etl_spark_error" {
  name           = "glue-etl-spark-error"
  pattern        = local.glue_etl_spark_metric_filter_error_pattern
  log_group_name = "${var.glue_etl_spark_log_group_name}/error"

  metric_transformation {
    name          = local.glue_etl_spark_error_metric_name
    namespace     = local.data_lake_namespace
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "glue_etl_pythonshell_error" {
  alarm_name          = "glue-etl-pythonshell-error"
  alarm_description   = "Errors logged over 1 minute by a Glue ETL pythonshell job."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.glue_etl_pythonshell_error.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.glue_etl_pythonshell_error.metric_transformation[0].namespace
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.cloudwatch_alarm_action.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_ok_action.arn]
}

resource "aws_cloudwatch_metric_alarm" "glue_etl_spark_error" {
  alarm_name          = "glue-etl-spark-error"
  alarm_description   = "Errors logged over 1 minute by a Glue ETL spark job."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.glue_etl_spark_error.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.glue_etl_spark_error.metric_transformation[0].namespace
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.cloudwatch_alarm_action.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_ok_action.arn]
}

resource "aws_cloudwatch_metric_alarm" "glue_job_failures" {
  alarm_name          = "glue-job-failures"
  alarm_description   = "Glue Job state has changed to `Failure`, `Timeout` or `Error`."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "MatchedEvents"
  namespace           = "AWS/Events"
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.cloudwatch_alarm_action.arn]
  ok_actions    = [aws_sns_topic.cloudwatch_ok_action.arn]

  dimensions = {
    RuleName = aws_cloudwatch_event_rule.glue_job_failure.name
  }
}
