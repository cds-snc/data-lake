locals {
  glue_role_arns = [
    aws_iam_role.glue_crawler.arn,
  ]
}

#
# KMS key used by AWS Glue for encryption
#
resource "aws_kms_key" "aws_glue" {
  description         = "AWS Glue encryption key for data at rest"
  enable_key_rotation = "true"
  policy              = data.aws_iam_policy_document.aws_glue.json
}

resource "aws_kms_alias" "data_export" {
  name          = "alias/aws-glue"
  target_key_id = aws_kms_key.aws_glue.key_id
}

data "aws_iam_policy_document" "aws_glue" {
  # checkov:skip=CKV_AWS_109: false-positive,`resources = ["*"]` references KMS key policy is attached to
  # checkov:skip=CKV_AWS_111: false-positive,`resources = ["*"]` references KMS key policy is attached to

  # Allow this account to use the key
  statement {
    effect    = "Allow"
    actions   = ["kms:*"]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = [var.account_id]
    }
  }

  # Allow product accounts to use the key for encryption
  statement {
    effect = "Allow"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:GenerateDataKeyWithoutPlaintext",
      "kms:ReEncryptFrom",
      "kms:ReEncryptTo",
      "kms:CreateGrant",
      "kms:DescribeKey",
      "kms:RetireGrant"
    ]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = local.glue_role_arns
    }
  }
}