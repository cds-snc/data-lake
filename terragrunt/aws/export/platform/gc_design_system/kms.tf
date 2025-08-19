#
# KMS key for GC Design System data export encryption
#
resource "aws_kms_key" "gc_design_system_exports" {
  description         = "KMS key for GC Design System data export encryption"
  enable_key_rotation = true
  policy              = data.aws_iam_policy_document.gc_design_system_exports_kms.json

  tags = {
    CostCentre = var.billing_tag_value
  }
}

resource "aws_kms_alias" "gc_design_system_exports" {
  name          = "alias/gc-design-system-exports"
  target_key_id = aws_kms_key.gc_design_system_exports.key_id
}

data "aws_iam_policy_document" "gc_design_system_exports_kms" {
  # checkov:skip=CKV_AWS_109: `resources = ["*"]` identifies the KMS key to which the key policy is attached
  # checkov:skip=CKV_AWS_111: `resources = ["*"]` identifies the KMS key to which the key policy is attached
  # checkov:skip=CKV_AWS_356: `resources = ["*"]` identifies the KMS key to which the key policy is attached

  statement {
    sid       = "Enable IAM User Permissions"
    effect    = "Allow"
    actions   = ["kms:*"]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"]
    }
  }

  statement {
    sid    = "Allow SQS service"
    effect = "Allow"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:CreateGrant",
      "kms:DescribeKey",
      "kms:RetireGrant"
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["sqs.amazonaws.com"]
    }
  }

  statement {
    sid    = "Allow Lambda service"
    effect = "Allow"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:CreateGrant",
      "kms:DescribeKey",
      "kms:RetireGrant"
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }

  statement {
    sid    = "Allow S3 service"
    effect = "Allow"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:CreateGrant",
      "kms:DescribeKey",
      "kms:RetireGrant"
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
  }

  statement {
    sid    = "Allow CloudWatch Logs"
    effect = "Allow"
    actions = [
      "kms:Encrypt*",
      "kms:Decrypt*",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*"
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["logs.${var.region}.amazonaws.com"]
    }
  }
}
