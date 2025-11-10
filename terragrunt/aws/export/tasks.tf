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

  env                               = var.env
  account_id                        = var.account_id
  region                            = var.region
  transformed_bucket_arn            = var.transformed_bucket_arn
  transformed_bucket_name           = var.transformed_bucket_name
  raw_bucket_arn                    = var.raw_bucket_arn
  raw_bucket_name                   = var.raw_bucket_name
  sns_topic_alarm_action_arn        = var.sns_topic_alarm_action_arn
  sns_topic_ok_action_arn           = var.sns_topic_ok_action_arn
  airtable_api_key                  = var.airtable_api_key
  airtable_base_id                  = var.airtable_base_id
  airtable_table_name_clients       = var.airtable_table_name_clients
  airtable_table_name_teams         = var.airtable_table_name_teams
  airtable_table_name_services      = var.airtable_table_name_services
  gc_design_system_crawler_arn      = var.gc_design_system_crawler_arn
  gc_design_system_crawler_name     = var.gc_design_system_crawler_name
  gc_design_system_npm_crawler_arn  = var.gc_design_system_npm_crawler_arn
  gc_design_system_npm_crawler_name = var.gc_design_system_npm_crawler_name

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

module "operations_google_analytics_export" {
  source = "./operations/google_analytics"

  env             = var.env
  account_id      = var.account_id
  region          = var.region
  raw_bucket_arn  = var.raw_bucket_arn
  raw_bucket_name = var.raw_bucket_name

  gcp_project_number                         = var.gcp_project_number
  gcp_pool_id                                = var.gcp_pool_id
  gcp_provider_id                            = var.gcp_provider_id
  gcp_service_account_email                  = var.gcp_service_account_email
  gcp_ga_property_forms_marketing_site       = var.gcp_ga_property_forms_marketing_site
  gcp_ga_property_notification_ga4           = var.gcp_ga_property_notification_ga4
  gcp_ga_property_platform_form_client       = var.gcp_ga_property_platform_form_client
  gcp_ga_property_platform_core_superset_doc = var.gcp_ga_property_platform_core_superset_doc

  billing_tag_value = var.billing_tag_value
}
