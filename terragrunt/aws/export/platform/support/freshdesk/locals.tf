locals {
  is_production = var.env == "production"

  cron_expression       = local.is_production ? "cron(0 5 * * ? *)" : "cron(0 0 1 1 1 1970)" # Daily at 5am UTC for prod, never otherwise
  freshdesk_export_path = "platform/support/freshdesk"
  freshdesk_lambda_name = "platform-support-freshdesk-export"
}