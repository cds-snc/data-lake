module "platform_support_freshdesk_export" {
  source = "./platform/support/freshdesk"

  freshdesk_api_key = var.freshdesk_api_key
  raw_bucket_arn    = var.raw_bucket_arn
  raw_bucket_name   = var.raw_bucket_name
  billing_tag_value = var.billing_tag_value
}
