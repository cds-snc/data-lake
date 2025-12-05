#
# Encrypt the Notify RDS Snapshot exports
#
resource "aws_kms_key" "platform_notify_rds_snapshot_exports" {
  description         = "Encrypt Notify RDS Snapshot exports"
  enable_key_rotation = true
  policy              = data.aws_iam_policy_document.platform_notify_rds_snapshot_exports_kms.json
}

resource "aws_kms_alias" "platform_notify_rds_snapshot_exports" {
  name          = "alias/platform-notify-rds-snapshot-exports"
  target_key_id = aws_kms_key.platform_notify_rds_snapshot_exports.key_id
}

data "aws_iam_policy_document" "platform_notify_rds_snapshot_exports_kms" {
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
      type = "AWS"
      identifiers = concat(
        [local.gc_notify_rds_export_role_arn],
        local.gc_notify_quicksight_role_arns,
      )
    }

    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}