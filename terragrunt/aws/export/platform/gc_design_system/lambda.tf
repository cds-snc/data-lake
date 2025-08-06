#
# GC Design System data export via a scheduled Lambda function
#
module "platform_gc_design_system_export" {
  source = "github.com/cds-snc/terraform-modules//lambda_schedule?ref=v10.6.2"

  lambda_name                = local.gc_design_system_lambda_name
  lambda_schedule_expression = local.cron_expression
  lambda_timeout             = "300"
  lambda_architectures       = ["arm64"]
  

  lambda_policies = [
    data.aws_iam_policy_document.platform_gc_design_system_export.json
  ]

  lambda_environment_variables = {
    AIRTABLE_API_KEY_PARAMETER_NAME = aws_ssm_parameter.airtable_api_key.name
    S3_BUCKET_NAME_TRANSFORMED      = var.transformed_bucket_name
    S3_BUCKET_NAME_RAW              = var.raw_bucket_name
    S3_OBJECT_PREFIX                = local.gc_design_system_export_path
    AIRTABLE_BASE_ID                = var.airtable_base_id
    AIRTABLE_TABLE_NAME             = var.airtable_table_name
    GLUE_CRAWLER_NAME               = var.gc_design_system_crawler_name
  }

  billing_tag_value = var.billing_tag_value
}

data "aws_iam_policy_document" "platform_gc_design_system_export" {
  statement {
    sid    = "GetSSMParameters"
    effect = "Allow"
    actions = [
      "ssm:GetParameter*",
    ]
    resources = [
      aws_ssm_parameter.airtable_api_key.arn
    ]
  }

  statement {
    sid    = "WriteToS3Bucket"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:DeleteObject"
    ]
    resources = [
      "${var.transformed_bucket_arn}/${local.gc_design_system_export_path}/*",
      "${var.raw_bucket_arn}/${local.gc_design_system_export_path}/*"
    ]
  }

  statement {
    sid    = "StartGlueCrawler"
    effect = "Allow"
    actions = [
      "glue:StartCrawler",
      "glue:GetCrawler"
    ]
    resources = [
      var.gc_design_system_crawler_arn
    ]
  }
}

resource "aws_ssm_parameter" "airtable_api_key" {
  name  = "/platform/gc-design-system/airtable-api-key"
  type  = "SecureString"
  value = var.airtable_api_key
}
