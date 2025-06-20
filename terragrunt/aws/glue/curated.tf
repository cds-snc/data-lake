#
# Platform / GC Notify / Curated
#
data "local_file" "platform_gc_notify_curated_job" {
  filename = "${path.module}/curated/platform/gc_notify/notification_enriched.py"
}

resource "aws_s3_object" "platform_gc_notify_curated_job" {
  bucket = var.glue_bucket_name
  key    = "curated/platform/gc_notify/notification_enriched.py"
  source = data.local_file.platform_gc_notify_curated_job.filename
  etag   = filemd5(data.local_file.platform_gc_notify_curated_job.filename)
}

resource "aws_glue_job" "platform_gc_notify_curated" {
  name = "Platform / GC Notify / Curated / Notification Enriched"

  glue_version           = "5.0"
  timeout                = 15 # minutes 
  role_arn               = aws_iam_role.glue_etl.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name
  worker_type            = "G.1X"
  number_of_workers      = 2

  command {
    script_location = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_gc_notify_curated_job.key}"
    python_version  = "3"
  }

  default_arguments = {
    "--continuous-log-logGroup"          = "/aws-glue/jobs/${aws_glue_security_configuration.encryption_at_rest.name}/service-role/${aws_iam_role.glue_etl.name}/output"
    "--continuous-log-logStreamPrefix"   = "platform_gc_notify_curated"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-auto-scaling"              = "true"
    "--enable-job-insights"              = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--job-language"                     = "python"
    "--curated_bucket"                   = var.curated_bucket_name
    "--curated_prefix"                   = "platform/gc-notify"
    "--enable-glue-datacatalog"          = "true"
    "--database_name_transformed"        = aws_glue_catalog_database.platform_gc_notify_production.name
    "--database_name_curated"            = aws_glue_catalog_database.platform_gc_notify_production_curated.name
    "--target_env"                       = var.env
    "--start_month"                      = " " # Default empty - will use current and previous month
    "--end_month"                        = " " # Default empty - will use current and previous month
  }
}
