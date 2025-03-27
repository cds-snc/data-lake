locals {
  gc_notify_env                 = "staging"
  gc_notify_lambda_name         = "platform-gc-notify-export"
  gc_notify_rds_export_role_arn = "arn:aws:iam::239043911459:role/NotifyExportToPlatformDataLake"
}