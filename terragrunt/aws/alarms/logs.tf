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

resource "aws_cloudwatch_query_definition" "glue_etl_pythonshell_errors" {
  name = "Glue ETL pythonshell - ERRORS"

  log_group_names = ["${var.glue_etl_pythonshell_log_group_name}/error"]

  query_string = <<-QUERY
    fields @timestamp, @message, @logStream
    | filter @message like /ERROR/
    | sort @timestamp desc
    | limit 100
  QUERY
}

resource "aws_cloudwatch_query_definition" "glue_etl_spark_errors" {
  name = "Glue ETL spark - ERRORS"

  log_group_names = ["${var.glue_etl_spark_log_group_name}/error"]

  query_string = <<-QUERY
    fields @timestamp, @message, @logStream
    | filter @message like /ERROR/
    | sort @timestamp desc
    | limit 100
  QUERY
}
