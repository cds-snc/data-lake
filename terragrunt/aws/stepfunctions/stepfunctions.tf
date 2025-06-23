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