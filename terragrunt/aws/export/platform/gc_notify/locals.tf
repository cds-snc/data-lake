locals {
  is_production = var.env == "production"

  cron_expression               = local.is_production ? "cron(0 4 ? * * *)" : "cron(0 0 1 1 ? 1970)" # Daily at 4am UTC for prod, never otherwise
  gc_notify_account_id          = local.is_production ? "296255494825" : "239043911459"
  gc_notify_env                 = var.env
  gc_notify_lambda_name         = "platform-gc-notify-export"
  gc_notify_rds_export_role_arn = "arn:aws:iam::${local.gc_notify_account_id}:role/NotifyExportToPlatformDataLake"
}