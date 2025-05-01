locals {
  gc_notify_env                 = "production"
  gc_notify_lambda_name         = "platform-gc-notify-export"
  gc_notify_rds_export_role_arn = "arn:aws:iam::296255494825:role/NotifyExportToPlatformDataLake"
}