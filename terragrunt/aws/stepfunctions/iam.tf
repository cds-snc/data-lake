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
  statement {
    effect = "Allow"
    actions = [
      "glue:StartJobRun",
      "glue:GetJobRun",
      "glue:GetJob"
    ]
    resources = [
      "arn:aws:glue:${var.region}:${var.account_id}:job/*"
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