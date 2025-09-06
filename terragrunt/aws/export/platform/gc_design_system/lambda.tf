#
# GC Design System data export via a scheduled Lambda function
#
module "platform_gc_design_system_export" {
  source = "github.com/cds-snc/terraform-modules//lambda_schedule?ref=v10.7.0"

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

#
# GC Design System NPM download data export via a scheduled Lambda function
#
module "platform_gc_design_system_npm_export" {
  source = "github.com/cds-snc/terraform-modules//lambda_schedule?ref=v10.7.0"

  lambda_name                = local.gc_design_system_npm_lambda_name
  lambda_schedule_expression = local.cron_expression
  lambda_timeout             = "300"
  lambda_architectures       = ["arm64"]

  lambda_policies = [
    data.aws_iam_policy_document.platform_gc_design_system_npm_export.json
  ]

  lambda_environment_variables = {
    S3_BUCKET_NAME_TRANSFORMED = var.transformed_bucket_name
    S3_BUCKET_NAME_RAW         = var.raw_bucket_name
    S3_OBJECT_PREFIX           = local.gc_design_system_npm_export_path
    GLUE_CRAWLER_NAME          = var.gc_design_system_npm_crawler_name
  }

  billing_tag_value = var.billing_tag_value
}

data "aws_iam_policy_document" "platform_gc_design_system_npm_export" {
  statement {
    sid    = "WriteToS3Bucket"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:DeleteObject"
    ]
    resources = [
      "${var.transformed_bucket_arn}/${local.gc_design_system_npm_export_path}/*",
      "${var.raw_bucket_arn}/${local.gc_design_system_npm_export_path}/*"
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
      var.gc_design_system_npm_crawler_arn
    ]
  }
}

#
# GC Design System CloudFront log processing via SQS-triggered Lambda function
#
module "platform_gc_design_system_cloudfront_export" {
  source = "github.com/cds-snc/terraform-modules//lambda_schedule?ref=v10.7.0"

  lambda_name                = local.gc_design_system_cloudfront_lambda_name
  lambda_schedule_expression = "rate(365 days)" # Effectively disabled - triggered by SQS instead
  lambda_timeout             = 900              # 15 minutes for batch processing
  lambda_architectures       = ["arm64"]

  lambda_policies = [
    data.aws_iam_policy_document.platform_gc_design_system_cloudfront_export.json
  ]

  lambda_environment_variables = {
    S3_BUCKET_NAME_TRANSFORMED = var.transformed_bucket_name
    S3_OBJECT_PREFIX           = local.gc_design_system_cloudfront_export_path
  }

  billing_tag_value = var.billing_tag_value
}

# SQS trigger for Lambda function
resource "aws_lambda_event_source_mapping" "cloudfront_sqs_trigger" {
  event_source_arn                   = aws_sqs_queue.cloudfront_processing_queue.arn
  function_name                      = module.platform_gc_design_system_cloudfront_export.lambda_function_arn
  batch_size                         = 50
  maximum_batching_window_in_seconds = 300
  enabled                            = local.is_production
}

data "aws_iam_policy_document" "platform_gc_design_system_cloudfront_export" {
  statement {
    sid    = "ReadFromS3RawBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject"
    ]
    resources = [
      "${var.raw_bucket_arn}/platform/gc-design-system/cloudfront-logs/*"
    ]
  }

  statement {
    sid    = "WriteToS3TransformedBucket"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl"
    ]
    resources = [
      "${var.transformed_bucket_arn}/${local.gc_design_system_cloudfront_export_path}/*"
    ]
  }

  statement {
    sid    = "ReceiveFromSQS"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes"
    ]
    resources = [
      aws_sqs_queue.cloudfront_processing_queue.arn
    ]
  }

  statement {
    sid    = "UseKMSForSQS"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey"
    ]
    resources = [
      aws_kms_key.gc_design_system_exports.arn
    ]
  }
}
