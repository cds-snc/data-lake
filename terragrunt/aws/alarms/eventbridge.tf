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

