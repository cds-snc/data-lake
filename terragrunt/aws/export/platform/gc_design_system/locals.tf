locals {
  is_production = var.env == "production"

  cron_expression                         = local.is_production ? "cron(0 5 * * ? *)" : "cron(0 0 1 1 ? 1970)" # Daily at 5am UTC for prod, never otherwise
  gc_design_system_lambda_name            = "platform-gc-design-system-airtable-export"
  gc_design_system_export_path            = "platform/gc-design-system/airtable"
  gc_design_system_npm_lambda_name        = "platform-gc-design-system-npm-export"
  gc_design_system_npm_export_path        = "platform/gc-design-system/npm"
  gc_design_system_cloudfront_lambda_name = "platform-gc-design-system-cloudfront-export"
  gc_design_system_cloudfront_export_path = "platform/gc-design-system/cloudfront-logs"
  gc_design_system_cloudfront_queue_name  = "platform-gc-design-system-cloudfront-processing"
}
