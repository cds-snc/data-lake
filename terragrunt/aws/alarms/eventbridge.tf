resource "aws_cloudwatch_event_rule" "glue_job_failure" {
  name        = "glue-job-failures"
  description = "Capture Glue job failures and timeouts"

  event_pattern = jsonencode({
    source      = ["aws.glue"]
    detail-type = ["Glue Job State Change"]
    detail = {
      state = ["FAILED", "TIMEOUT", "ERROR"]
    }
  })
}

resource "aws_cloudwatch_event_target" "glue_job_failure" {
  rule      = aws_cloudwatch_event_rule.glue_job_failure.name
  target_id = "PublishMetric"
  arn       = "arn:aws:events:${var.region}:${var.account_id}:api-destination/cloudwatch-metrics"

  input_transformer {
    input_paths = {
      jobName = "$.detail.jobName"
      state   = "$.detail.state"
    }
    input_template = jsonencode({
      MetricData = [{
        MetricName = local.glue_job_failure_metric_name
        Value      = 1
        Unit       = "Count"
        Dimensions = [{
          Name  = "JobName"
          Value = "<jobName>"
        }]
      }]
      Namespace = local.data_lake_namespace
    })
  }
}
