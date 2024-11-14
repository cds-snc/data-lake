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

#
# Publish Glue Job failures to SNS using a CloudWatch Alarm message payload.
# This allows us to use the existing SRE Bot webhooks to post to Slack.
#
resource "aws_cloudwatch_event_target" "glue_job_failure" {
  rule      = aws_cloudwatch_event_rule.glue_job_failure.name
  target_id = "send-to-sns"
  arn       = aws_sns_topic.cloudwatch_alarm_action.arn

  input_transformer {
    input_paths = {
      jobName = "$.detail.jobName"
      state   = "$.detail.state"
      message = "$.detail.message"
    }
    input_template = jsonencode({
      Message = jsonencode({
        AlarmArn         = "arn:aws:cloudwatch:${var.region}:${var.account_id}:alarm:glue-job-failure",
        AlarmName        = "glue-job-failure",
        AlarmDescription = "`<state>` detected for Glue job `<jobName>`",
        AWSAccountId     = var.account_id,
        OldStateValue    = "OK",
        NewStateValue    = "ALARM",
        NewStateReason   = "<message>",
      })
    })
  }
}
