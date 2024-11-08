#
# SNS topics
#
resource "aws_sns_topic" "cloudwatch_alarm_action" {
  name              = "cloudwatch-alarm-action"
  kms_master_key_id = aws_kms_key.cloudwatch.arn
}

resource "aws_sns_topic" "cloudwatch_ok_action" {
  name              = "cloudwatch-ok-action"
  kms_master_key_id = aws_kms_key.cloudwatch.arn
}

#
# SNS topic subscriptions
#
resource "aws_sns_topic_subscription" "cloudwatch_alarm_action" {
  topic_arn = aws_sns_topic.cloudwatch_alarm_action.arn
  protocol  = "https"
  endpoint  = var.cloudwatch_alarm_slack_webhook
}

resource "aws_sns_topic_subscription" "cloudwatch_ok_action" {
  topic_arn = aws_sns_topic.cloudwatch_ok_action.arn
  protocol  = "https"
  endpoint  = var.cloudwatch_alarm_slack_webhook
}

#
# Allow CloudWatch to use the SNS topics
#
resource "aws_sns_topic_policy" "cloudwatch_alarm_action" {
  arn    = aws_sns_topic.cloudwatch_alarm_action.arn
  policy = data.aws_iam_policy_document.cloudwatch_events_sns_topic.json
}

resource "aws_sns_topic_policy" "cloudwatch_ok_action" {
  arn    = aws_sns_topic.cloudwatch_ok_action.arn
  policy = data.aws_iam_policy_document.cloudwatch_events_sns_topic.json
}

data "aws_iam_policy_document" "cloudwatch_events_sns_topic" {
  statement {
    # checkov:skip=CKV_AWS_111: False-positive, `resources = ["*"]` refers to the SNS topic the policy applies to 
    # checkov:skip=CKV_AWS_356: False-positive, `resources = ["*"]` refers to the SNS topic the policy applies to 
    sid    = "SNS_Default_Policy"
    effect = "Allow"
    actions = [
      "SNS:Subscribe",
      "SNS:SetTopicAttributes",
      "SNS:RemovePermission",
      "SNS:Receive",
      "SNS:Publish",
      "SNS:ListSubscriptionsByTopic",
      "SNS:GetTopicAttributes",
      "SNS:DeleteTopic",
      "SNS:AddPermission",
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceOwner"
      values   = [var.account_id]
    }

    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }

  statement {
    sid    = "SNS_Publish_statement"
    effect = "Allow"
    actions = [
      "sns:Publish"
    ]

    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}