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


module "operations_google_analytics_export" {
  source = "github.com/cds-snc/terraform-modules//lambda_schedule?ref=v10.10.2"

  lambda_name                = local.google_analytics_lambda_name
  lambda_schedule_expression = local.cron_expression
  lambda_timeout             = "60"
  lambda_architectures       = ["arm64"]

  lambda_policies = [
    data.aws_iam_policy_document.operations_google_analytics_export.json
  ]

  lambda_assume_role_policies = [
    data.aws_iam_policy_document.assume_role_web_identity.json
  ]

  lambda_environment_variables = {
    S3_BUCKET_NAME                             = var.raw_bucket_name
    S3_EXPORT_PREFIX                           = "operations/google-analytics"
    GCP_PROJECT_NUMBER                         = var.gcp_project_number
    GCP_POOL_ID                                = var.gcp_pool_id
    GCP_PROVIDER_ID                            = var.gcp_provider_id
    GCP_SERVICE_ACCOUNT_EMAIL                  = var.gcp_service_account_email
    GCP_GA_PROPERTY_FORMS_MARKETING_SITE       = var.gcp_ga_property_forms_marketing_site
    GCP_GA_PROPERTY_NOTIFICATION_GA4           = var.gcp_ga_property_notification_ga4
    GCP_GA_PROPERTY_PLATFORM_FORM_CLIENT       = var.gcp_ga_property_platform_form_client
    GCP_GA_PROPERTY_PLATFORM_CORE_SUPERSET_DOC = var.gcp_ga_property_platform_core_superset_doc
  }

  billing_tag_value = var.billing_tag_value
}

data "aws_iam_policy_document" "operations_google_analytics_export" {
  statement {
    sid    = "S3WriteAccess"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
    ]
    resources = [
      "arn:aws:s3:::${var.raw_bucket_name}/operations/google-analytics/*"
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
      values   = ["operations/google-analytics/*"]
    }
  }
}