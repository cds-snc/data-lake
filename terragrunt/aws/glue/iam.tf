#
# Glue crawler role
#
resource "aws_iam_role" "glue_crawler" {
  name               = "AWSGlueCrawler-DataLake"
  path               = "/service-role/"
  assume_role_policy = data.aws_iam_policy_document.glue_crawler_assume.json
}

resource "aws_iam_policy" "glue_crawler" {
  name   = "AWSGlueCrawler-DataLake"
  path   = "/service-role/"
  policy = data.aws_iam_policy_document.glue_crawler.json
}

resource "aws_iam_role_policy_attachment" "glue_crawler" {
  policy_arn = aws_iam_policy.glue_crawler.arn
  role       = aws_iam_role.glue_crawler.name
}

resource "aws_iam_role_policy_attachment" "aws_glue_service_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
  role       = aws_iam_role.glue_crawler.name
}

data "aws_iam_policy_document" "glue_crawler_assume" {
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

data "aws_iam_policy_document" "glue_crawler" {
  statement {
    sid = "ReadDataLakeS3Buckets"
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${var.curated_bucket_arn}/*",
      "${var.raw_bucket_arn}/*",
      "${var.transformed_bucket_arn}/*"
    ]
  }

  statement {
    sid    = "UseGlueKey"
    effect = "Allow"
    actions = [
      "kms:CreateGrant",
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:GenerateDataKeyWithoutPlaintext",
      "kms:ReEncryptFrom",
      "kms:ReEncryptTo",
      "kms:RetireGrant"
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
      "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws-glue/crawlers-role/service-role/${aws_iam_role.glue_crawler.name}-${aws_glue_security_configuration.encryption_at_rest.name}:*"
    ]
  }
}
