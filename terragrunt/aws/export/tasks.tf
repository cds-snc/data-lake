module "platform_notify_export" {
  source = "./platform/notify"

  account_id = var.account_id
}

module "platform_support_freshdesk_export" {
  source = "./platform/support/freshdesk"

  freshdesk_api_key          = var.freshdesk_api_key
  raw_bucket_arn             = var.raw_bucket_arn
  raw_bucket_name            = var.raw_bucket_name
  sns_topic_alarm_action_arn = var.sns_topic_alarm_action_arn
  sns_topic_ok_action_arn    = var.sns_topic_ok_action_arn

  billing_tag_value = var.billing_tag_value
}
