#
# Google Analytics data exports to the Data Lake's Raw bucket
#


data "aws_iam_policy_document" "assume_role_web_identity" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = ["arn:aws:iam::${var.account_id}:oidc-provider/sts.amazonaws.com"]
    }
  }
}


module "platform_google_analytics_export" {
  source = "github.com/cds-snc/terraform-modules//lambda_schedule?ref=v10.8.6"

  lambda_name                = local.google_analytics_lambda_name
  lambda_schedule_expression = local.cron_expression
  lambda_timeout             = "60"
  lambda_architectures       = ["arm64"]

  lambda_policies = [
    data.aws_iam_policy_document.platform_google_analytics_export.json
  ]

  lambda_assume_role_policies = [
    data.aws_iam_policy_document.assume_role_web_identity.json
  ]

  lambda_environment_variables = {
    S3_BUCKET_NAME   = var.raw_bucket_name
    S3_EXPORT_PREFIX = "platform/google-analytics"
  }

  billing_tag_value = var.billing_tag_value
}

data "aws_iam_policy_document" "platform_google_analytics_export" {
  statement {
    sid    = "S3WriteAccess"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
    ]
    resources = [
      "arn:aws:s3:::${var.raw_bucket_name}/platform/google-analytics/*"
    ]
  }

  statement {
    sid    = "S3ListAccess"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.raw_bucket_name}"
    ]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["platform/google-analytics/*"]
    }
  }
}