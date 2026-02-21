#
# Freshdesk export via a scheduled Lambda function
#
module "platform_support_freshdesk_export" {
  source = "github.com/cds-snc/terraform-modules//lambda_schedule?ref=v10.11.0"

  lambda_name                = local.freshdesk_lambda_name
  lambda_schedule_expression = local.cron_expression
  lambda_timeout             = "900"
  lambda_architectures       = ["arm64"]
  s3_arn_write_path          = "${var.raw_bucket_arn}/${local.freshdesk_export_path}/*"

  lambda_policies = [
    data.aws_iam_policy_document.platform_support_freshdesk_export.json
  ]

  lambda_environment_variables = {
    FRESHDESK_API_KEY_PARAMETER_NAME = aws_ssm_parameter.freshdesk_api_key.name
    FRESHDESK_DOMAIN                 = "cds-snc.freshdesk.com"
    S3_BUCKET_NAME                   = var.raw_bucket_name
    S3_OBJECT_PREFIX                 = local.freshdesk_export_path
  }

  billing_tag_value = var.billing_tag_value
}

data "aws_iam_policy_document" "platform_support_freshdesk_export" {
  statement {
    sid    = "GetSSMParameters"
    effect = "Allow"
    actions = [
      "ssm:GetParameter*",
    ]
    resources = [
      aws_ssm_parameter.freshdesk_api_key.arn
    ]
  }
}

resource "aws_ssm_parameter" "freshdesk_api_key" {
  name  = "/platform/support/freshdesk-api-key"
  type  = "SecureString"
  value = var.freshdesk_api_key
}
