module "platform_notify_export" {
  source = "./platform/gc_notify"

  env                        = var.env
  account_id                 = var.account_id
  raw_bucket_name            = var.raw_bucket_name
  sns_topic_alarm_action_arn = var.sns_topic_alarm_action_arn
  sns_topic_ok_action_arn    = var.sns_topic_ok_action_arn

  billing_tag_value = var.billing_tag_value
}

module "platform_gc_design_system_export" {
  source = "./platform/gc_design_system"

  env                        = var.env
  account_id                 = var.account_id
  region                     = var.region
  transformed_bucket_arn     = var.transformed_bucket_arn
  transformed_bucket_name    = var.transformed_bucket_name
  raw_bucket_arn             = var.raw_bucket_arn
  raw_bucket_name            = var.raw_bucket_name
  sns_topic_alarm_action_arn = var.sns_topic_alarm_action_arn
  sns_topic_ok_action_arn    = var.sns_topic_ok_action_arn
  airtable_api_key           = var.airtable_api_key

  billing_tag_value = var.billing_tag_value
}

module "platform_support_freshdesk_export" {
  source = "./platform/support/freshdesk"

  env                        = var.env
  freshdesk_api_key          = var.freshdesk_api_key
  raw_bucket_arn             = var.raw_bucket_arn
  raw_bucket_name            = var.raw_bucket_name
  sns_topic_alarm_action_arn = var.sns_topic_alarm_action_arn
  sns_topic_ok_action_arn    = var.sns_topic_ok_action_arn

  billing_tag_value = var.billing_tag_value
}
