#
# GC Notify RDS snapshot exports to the Data Lake's Raw bucket
#
module "platform_gc_notify_export" {
  source = "github.com/cds-snc/terraform-modules//lambda_schedule?ref=v10.8.3"

  lambda_name                = local.gc_notify_lambda_name
  lambda_schedule_expression = local.cron_expression
  lambda_timeout             = "60"
  lambda_architectures       = ["arm64"]

  lambda_policies = [
    data.aws_iam_policy_document.platform_gc_notify_export.json
  ]

  lambda_environment_variables = {
    DB_CLUSTER_IDENTIFIER = "notification-canada-ca-${local.gc_notify_env}-cluster"
    IAM_ROLE_ARN          = local.gc_notify_rds_export_role_arn
    KMS_KEY_ID            = aws_kms_key.platform_notify_rds_snapshot_exports.arn
    TABLE_SCHEMA          = "NotificationCanadaCa${local.gc_notify_env}.public"
    S3_BUCKET_NAME        = var.raw_bucket_name
    S3_EXPORT_PREFIX      = "platform/gc-notify"
  }

  billing_tag_value = var.billing_tag_value
}

data "aws_iam_policy_document" "platform_gc_notify_export" {
  statement {
    sid    = "STSAssumeRole"
    effect = "Allow"
    actions = [
      "sts:AssumeRole",
    ]
    resources = [local.gc_notify_rds_export_role_arn]
  }
}
