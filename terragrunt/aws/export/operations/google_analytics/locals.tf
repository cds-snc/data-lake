locals {
  is_production = var.env == "production"

  cron_expression              = local.is_production ? "cron(0 6 ? * * *)" : "cron(0 0 1 1 ? 1970)" # Daily at 6am UTC for prod, never otherwise
  google_analytics_lambda_name = "operations-google-analytics-export"
}