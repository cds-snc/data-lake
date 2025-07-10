data "template_file" "data_orchestrator_state_machine" {
  template = file("${path.module}/state_machines/data_lake_orchestrator.json")

  vars = {
    platform_gc_forms_job_name          = var.platform_gc_forms_job_name
    platform_gc_notify_job_name         = var.platform_gc_notify_job_name
    platform_support_freshdesk_name     = var.platform_support_freshdesk_name
    platform_gc_notify_curated_job_name = var.platform_gc_notify_curated_job_name
    bes_crm_salesforce_name             = var.bes_crm_salesforce_name
    transformed_bucket_name             = var.transformed_bucket_name
  }
}

resource "aws_sfn_state_machine" "data_orchestrator" {
  name       = "DataLakeOrchestrator"
  role_arn   = aws_iam_role.sfn_role.arn
  definition = data.template_file.data_orchestrator_state_machine.rendered
}

# CloudWatch EventBridge rule to trigger the state machine at 2AM daily
# Enabled in production, disabled in staging for testing
resource "aws_cloudwatch_event_rule" "data_orchestrator_schedule" {
  name                = "data-orchestrator-daily-schedule"
  description         = "Trigger DataLakeOrchestrator state machine daily at 2AM UTC"
  schedule_expression = "cron(0 7 * * ? *)" # Daily at 7am UTC
  state               = var.env == "production" ? "ENABLED" : "DISABLED"
}

# CloudWatch EventBridge target to execute the state machine
resource "aws_cloudwatch_event_target" "data_orchestrator_target" {
  rule      = aws_cloudwatch_event_rule.data_orchestrator_schedule.name
  target_id = "DataOrchestratorTarget"
  arn       = aws_sfn_state_machine.data_orchestrator.arn
  role_arn  = aws_iam_role.eventbridge_sfn_role.arn
}