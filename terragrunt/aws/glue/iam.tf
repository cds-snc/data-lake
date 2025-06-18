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
    data.aws_iam_policy_document.cloudwatch_metrics.json,
    data.aws_iam_policy_document.glue_pass_role.json
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

# Allow Glue ETL role to pass itself to Glue jobs
data "aws_iam_policy_document" "glue_pass_role" {
  statement {
    sid = "PassGlueETLRole"
    actions = [
      "iam:PassRole"
    ]
    resources = [
      "arn:aws:iam::${var.account_id}:role/service-role/AWSGlueETL-DataLake"
#
# BES Strategic Data
# Grants access to the `bes/strategic-data/*` S3 prefix and related Glue and Athena resources.
#
resource "aws_iam_policy" "bes_strategic_data_access" {
  name   = "bes-strategic-data-access"
  path   = "/"
  policy = data.aws_iam_policy_document.bes_strategic_data_access.json
}

data "aws_iam_policy_document" "bes_strategic_data_access" {
  version = "2012-10-17"

  statement {
    sid    = "S3ListBuckets"
    effect = "Allow"
    actions = [
      "s3:GetBucketVersioning",
      "s3:ListAllMyBuckets"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "S3ListObjects"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:ListBucketVersions"
    ]
    resources = [
      var.raw_bucket_arn,
      var.transformed_bucket_arn
    ]
    condition {
      test     = "ForAnyValue:StringLike"
      variable = "s3:prefix"
      values = [
        "",
        "${local.s3_bes_prefix}/",
        "${local.s3_bes_strategic_data_prefix}/*"
      ]
    }
  }

  statement {
    sid    = "S3ObjectsReadWrite"
    effect = "Allow"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
      "s3:GetObject",
      "s3:GetObjectAcl",
      "s3:GetObjectTagging",
      "s3:GetObjectVersion",
      "s3:GetObjectVersionTagging",
      "s3:ListBucketVersions",
      "s3:ListMultipartUploadParts",
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:PutObjectTagging",
      "s3:PutObjectVersionAcl",
      "s3:PutObjectVersionTagging"
    ]
    resources = [
      "${var.raw_bucket_arn}/${local.s3_bes_strategic_data_prefix}/*",
      "${var.transformed_bucket_arn}/${local.s3_bes_strategic_data_prefix}/*",
    ]
  }

  statement {
    sid    = "AthenaAccess"
    effect = "Allow"
    actions = [
      "athena:ListWorkGroups",
      "athena:GetWorkGroup",
      "athena:StartQueryExecution",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:StopQueryExecution",
      "athena:ListQueryExecutions",
      "athena:BatchGetQueryExecution"
    ]
    resources = [
      "arn:aws:athena:${var.region}:${var.account_id}:workgroup/data-lake-${var.env}"
    ]
  }

  statement {
    sid    = "GlueTableReadAccess"
    effect = "Allow"
    actions = [
      "glue:GetColumnStatisticsTaskRuns",
      "glue:GetTable",
      "glue:GetTableVersion",
      "glue:GetTableVersions",
      "glue:GetTables",
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetPartitions",
      "glue:SearchTables"
    ]
    resources = [
      "arn:aws:glue:${var.region}:${var.account_id}:catalog",
      "arn:aws:glue:${var.region}:${var.account_id}:database/${aws_glue_catalog_database.bes_strategic_data_production.name}",
      "arn:aws:glue:${var.region}:${var.account_id}:database/${aws_glue_catalog_database.bes_strategic_data_production_raw.name}",
      "arn:aws:glue:${var.region}:${var.account_id}:table/${aws_glue_catalog_database.bes_strategic_data_production.name}/*",
      "arn:aws:glue:${var.region}:${var.account_id}:table/${aws_glue_catalog_database.bes_strategic_data_production_raw.name}/*"
    ]
  }

  statement {
    sid    = "AthenaResultsAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]
    resources = [
      var.athena_bucket_arn,
      "${var.athena_bucket_arn}/*",
    ]
  }
}