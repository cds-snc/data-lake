resource "aws_iam_role" "platform_notify_rds_snapshot_exports" {
  name               = "platform-notify-export"
  description        = "Trigger exports of Notify RDS snapshots to the Data Lake"
  assume_role_policy = data.aws_iam_policy_document.platform_notify_rds_snapshot_exports_assume.json
}

resource "aws_iam_policy" "platform_notify_rds_snapshot_exports" {
  name   = "platform-notify-export"
  policy = data.aws_iam_policy_document.platform_notify_rds_snapshot_exports.json
}

resource "aws_iam_role_policy_attachment" "platform_notify_rds_snapshot_exports" {
  role       = aws_iam_role.platform_notify_rds_snapshot_exports.name
  policy_arn = aws_iam_policy.platform_notify_rds_snapshot_exports.arn
}

data "aws_iam_policy_document" "platform_notify_rds_snapshot_exports_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com"
      ]
    }
  }
}

data "aws_iam_policy_document" "platform_notify_rds_snapshot_exports" {
  statement {
    sid    = "STSAssumeRole"
    effect = "Allow"
    actions = [
      "sts:AssumeRole",
    ]
    resources = local.notify_rds_export_role_arns
  }
}