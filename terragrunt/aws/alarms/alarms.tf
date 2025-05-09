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
resource "aws_cloudwatch_log_metric_filter" "glue_etl_error" {
  name           = "glue-etl-error"
  pattern        = local.glue_etl_metric_filter_error_pattern
  log_group_name = "${var.glue_etl_log_group_name}/output"

  metric_transformation {
    name          = local.glue_etl_error_metric_name
    namespace     = local.data_lake_namespace
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "glue_etl_error" {
  alarm_name          = "glue-etl-error"
  alarm_description   = "Errors logged over 1 minute by a Glue ETL job."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.glue_etl_error.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.glue_etl_error.metric_transformation[0].namespace
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

resource "aws_cloudwatch_metric_alarm" "platform_gc_forms_etl_user_processed_record_anomaly" {
  alarm_name          = "platform-gc-forms-etl-user-processed-record-anomaly"
  alarm_description   = "'Platform / GC Forms' ETL job anomaly detection for the 'user' dataset."
  comparison_operator = "LessThanLowerOrGreaterThanUpperThreshold"
  threshold_metric_id = "processed_records_expected"
  evaluation_periods  = 1
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "processed_records_expected"
    expression  = "ANOMALY_DETECTION_BAND(processed_records, 0.5)" # standard deviations
    label       = "Processed Records (Expected)"
    return_data = "true"
  }

  metric_query {
    id          = "processed_records"
    return_data = "true"
    metric {
      metric_name = "ProcessedRecordCount"
      namespace   = "data-lake/etl/gc-forms"
      period      = 86400 # 1 day
      stat        = "Sum"
      unit        = "Count"

      dimensions = {
        Dataset = "processed-data/user"
      }
    }
  }
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