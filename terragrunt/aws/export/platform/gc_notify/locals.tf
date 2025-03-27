locals {
  notify_env                         = "staging"
  notify_rds_export_staging_role_arn = "arn:aws:iam::239043911459:role/NotifyExportToPlatformDataLake"
  notify_rds_export_role_arns = [
    local.notify_rds_export_staging_role_arn
  ]
}