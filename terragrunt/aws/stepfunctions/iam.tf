data "aws_iam_policy_document" "sfn_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sfn_role" {
  name               = "StepFunctionsRole"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume_role.json
}

data "aws_iam_policy_document" "sfn_glue_policy" {
  # Glue job permissions
  statement {
    effect = "Allow"
    actions = [
      "glue:StartJobRun",
      "glue:GetJobRun",
      "glue:GetJob",
      "glue:BatchStopJobRun",
      "glue:GetJobRuns"
    ]
    resources = [
      "arn:aws:glue:${var.region}:${var.account_id}:job/*"
    ]
  }

  # Glue catalog permissions 
  statement {
    effect = "Allow"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:CreateTable",
      "glue:UpdateTable",
      "glue:DeleteTable",
      "glue:GetPartitions",
      "glue:GetPartition",
      "glue:BatchGetPartition"
    ]
    resources = [
      "arn:aws:glue:${var.region}:${var.account_id}:catalog",
      "arn:aws:glue:${var.region}:${var.account_id}:database/*",
      "arn:aws:glue:${var.region}:${var.account_id}:table/*"
    ]
  }

  # S3 permissions read
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]
    resources = [
      "arn:aws:s3:::${var.transformed_bucket_name}",
      "arn:aws:s3:::${var.transformed_bucket_name}/*"
    ]
  }

  # S3 permissions read/write/delete
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts"
    ]
    resources = [
      "arn:aws:s3:::${var.curated_bucket_name}",
      "arn:aws:s3:::${var.curated_bucket_name}/*"
    ]
  }

}

resource "aws_iam_policy" "sfn_glue_policy" {
  name   = "StepFunctionsGluePolicy"
  policy = data.aws_iam_policy_document.sfn_glue_policy.json
}

resource "aws_iam_role_policy_attachment" "sfn_glue_policy_attachment" {
  role       = aws_iam_role.sfn_role.name
  policy_arn = aws_iam_policy.sfn_glue_policy.arn
}