#
# Resource policy for the Glue Data Catalog
#
resource "aws_glue_resource_policy" "cross_account_access" {
  policy = data.aws_iam_policy_document.cross_account_access_combined.json
}

data "aws_iam_policy_document" "cross_account_access_combined" {
  source_policy_documents = [
    for policy in data.aws_iam_policy_document.cross_account_access : policy.json
  ]
}

data "aws_iam_policy_document" "cross_account_access" {
  for_each = local.glue_catalog_databases_superset_access

  statement {
    sid = "SupersetReadAccess${join("", [for word in split("_", replace(each.value, "/[^a-zA-Z0-9_]/", "")) : title(word)])}"
    principals {
      type        = "AWS"
      identifiers = [for arn in var.superset_iam_role_arns : arn if endswith(arn, each.value)]
    }
    actions = [
      "glue:BatchGetPartition",
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:GetTable",
      "glue:GetTables",
      "glue:GetTableVersion",
      "glue:GetTableVersions"
    ]
    resources = [
      "arn:aws:glue:${var.region}:${var.account_id}:catalog",
      "arn:aws:glue:${var.region}:${var.account_id}:database/${each.value}",
      "arn:aws:glue:${var.region}:${var.account_id}:table/${each.value}/*",
    ]
  }
}

#
# Glue crawler role
#
resource "aws_iam_role" "glue_crawler" {
  name               = "AWSGlueCrawler-DataLake"
  path               = "/service-role/"
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
}

resource "aws_iam_policy" "glue_crawler" {
  name   = "AWSGlueCrawler-DataLake"
  path   = "/service-role/"
  policy = data.aws_iam_policy_document.glue_crawler_combined.json
}

data "aws_iam_policy_document" "glue_crawler_combined" {
  source_policy_documents = [
    data.aws_iam_policy_document.s3_read_data_lake.json,
    data.aws_iam_policy_document.glue_kms.json
  ]
}

resource "aws_iam_role_policy_attachment" "glue_crawler" {
  policy_arn = aws_iam_policy.glue_crawler.arn
  role       = aws_iam_role.glue_crawler.name
}

resource "aws_iam_role_policy_attachment" "aws_glue_service_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
  role       = aws_iam_role.glue_crawler.name
}

#
# Glue ETL role
#
resource "aws_iam_role" "glue_etl" {
  name               = "AWSGlueETL-DataLake"
  path               = "/service-role/"
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
}

resource "aws_iam_policy" "glue_etl" {
  name   = "AWSGlueETL-DataLake"
  path   = "/service-role/"
  policy = data.aws_iam_policy_document.glue_etl_combined.json
}

data "aws_iam_policy_document" "glue_etl_combined" {
  source_policy_documents = [
    data.aws_iam_policy_document.s3_read_data_lake.json,
    data.aws_iam_policy_document.s3_write_data_lake.json,
    data.aws_iam_policy_document.glue_kms.json,
    data.aws_iam_policy_document.gc_notify_rds_export_kms.json,
    data.aws_iam_policy_document.cloudwatch_metrics.json
  ]
}

resource "aws_iam_role_policy_attachment" "glue_etl" {
  policy_arn = aws_iam_policy.glue_etl.arn
  role       = aws_iam_role.glue_etl.name
}

resource "aws_iam_role_policy_attachment" "glue_etl_service_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
  role       = aws_iam_role.glue_etl.name
}

#
# Custom policies
#
data "aws_iam_policy_document" "glue_assume" {
  statement {
    actions = [
      "sts:AssumeRole",
    ]
    principals {
      type = "Service"
      identifiers = [
        "glue.amazonaws.com",
      ]
    }
  }
}

data "aws_iam_policy_document" "s3_read_data_lake" {
  statement {
    sid = "ReadDataLakeS3Buckets"
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${var.curated_bucket_arn}/*",
      "${var.glue_bucket_arn}/*",
      "${var.raw_bucket_arn}/*",
      "${var.transformed_bucket_arn}/*"
    ]
  }
}

data "aws_iam_policy_document" "glue_kms" {
  statement {
    sid    = "UseGlueKey"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:GenerateDataKeyWithoutPlaintext",
      "kms:ReEncryptFrom",
      "kms:ReEncryptTo",
    ]
    resources = [
      aws_kms_key.aws_glue.arn
    ]
  }

  statement {
    sid    = "AssociateKmsKey"
    effect = "Allow"
    actions = [
      "logs:AssociateKmsKey"
    ]
    resources = [
      "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws-glue/crawlers*",
      "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws-glue/jobs*",
      "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws-glue/python-jobs*",
      "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws-glue/sessions*"
    ]
  }
}

data "aws_iam_policy_document" "gc_notify_rds_export_kms" {
  statement {
    sid    = "UseNotifyRdsExportKey"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:GenerateDataKeyWithoutPlaintext",
      "kms:ReEncryptFrom",
      "kms:ReEncryptTo",
    ]
    resources = [
      "arn:aws:kms:${var.region}:${var.account_id}:key/*"
    ]
    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/platform-notify-rds-snapshot-exports"]
    }
  }
}

data "aws_iam_policy_document" "s3_write_data_lake" {
  statement {
    sid = "WriteDataLakeS3TransformedBuckets"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = [
      "${var.curated_bucket_arn}/*",
      "${var.transformed_bucket_arn}/*",
      "${var.raw_bucket_arn}/*"
    ]
  }
}

data "aws_iam_policy_document" "cloudwatch_metrics" {
  statement {
    sid    = "CloudWatchMetrics"
    effect = "Allow"
    actions = [
      "cloudwatch:GetMetricData",
      "cloudwatch:GetMetricStatistics",
      "cloudwatch:PutMetricData",
    ]
    resources = [
      "*" # Only wildcard is allowed for this action
    ]
  }
}