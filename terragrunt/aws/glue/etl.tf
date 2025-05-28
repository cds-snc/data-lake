#
# Platform / GC Forms
#
data "local_file" "platform_gc_forms_job" {
  filename = "${path.module}/etl/platform/gc_forms/process_data.py"
}

resource "aws_s3_object" "platform_gc_forms_job" {
  bucket = var.glue_bucket_name
  key    = "platform/gc_forms/process_data.py"
  source = data.local_file.platform_gc_forms_job.filename
  etag   = filemd5(data.local_file.platform_gc_forms_job.filename)
}

data "archive_file" "platform_gc_forms_gx" {
  type        = "zip"
  source_dir  = "${path.module}/etl/platform/gc_forms/gx"
  output_path = "${path.module}/etl/platform/gc_forms/gx.zip"
}

resource "aws_s3_object" "platform_gc_forms_gx" {
  bucket = var.glue_bucket_name
  key    = "platform/gc_forms/gx.zip"
  source = data.archive_file.platform_gc_forms_gx.output_path
  etag   = data.archive_file.platform_gc_forms_gx.output_md5
}

resource "aws_glue_job" "platform_gc_forms_job" {
  name = "Platform / GC Forms"

  glue_version           = "5.0"
  timeout                = 15 # minutes
  role_arn               = aws_iam_role.glue_etl.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name
  max_capacity           = 1

  command {
    script_location = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_gc_forms_job.key}"
    python_version  = "3.9"
    name            = "pythonshell"
  }

  default_arguments = {
    "--additional-python-modules"        = "great_expectations==0.18.22"
    "--continuous-log-logGroup"          = "/aws-glue/python-jobs/${aws_glue_security_configuration.encryption_at_rest.name}/service-role/${aws_iam_role.glue_etl.name}/output"
    "--continuous-log-logStreamPrefix"   = "platform_gc_forms"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-auto-scaling"              = "true"
    "--enable-job-insights"              = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--first_date"                       = "yesterday"
    "--last_date"                        = "yesterday"
    "--gx_config_object"                 = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_gc_forms_gx.key}"
    "--job-language"                     = "python"
    "--source_bucket"                    = var.raw_bucket_name
    "--source_prefix"                    = "platform/gc-forms"
    "--transformed_bucket"               = var.transformed_bucket_name
    "--transformed_prefix"               = "platform/gc-forms"
    "--database_name_raw"                = aws_glue_catalog_database.platform_gc_forms_production_raw.name
    "--database_name_transformed"        = aws_glue_catalog_database.platform_gc_forms_production.name
    "--table_name_prefix"                = "platform_gc_forms"
  }
}

resource "aws_glue_trigger" "platform_gc_forms_job" {
  name     = "Platform / GC Forms"
  schedule = "cron(00 2 * * ? *)" # 2am UTC every day
  type     = "SCHEDULED"
  enabled  = local.is_production

  actions {
    job_name = aws_glue_job.platform_gc_forms_job.name
  }
}

#
# Platform / GC Notify
#
data "local_file" "platform_gc_notify_job" {
  filename = "${path.module}/etl/platform/gc_notify/process_data.py"
}

resource "aws_s3_object" "platform_gc_notify_job" {
  bucket = var.glue_bucket_name
  key    = "platform/gc_notify/process_data.py"
  source = data.local_file.platform_gc_notify_job.filename
  etag   = filemd5(data.local_file.platform_gc_notify_job.filename)
}

data "local_file" "platform_gc_notify_requirements" {
  filename = "${path.module}/etl/platform/gc_notify/requirements.txt"
}

resource "aws_s3_object" "platform_gc_notify_requirements" {
  bucket = var.glue_bucket_name
  key    = "platform/gc_notify/requirements.txt"
  source = data.local_file.platform_gc_notify_requirements.filename
  etag   = filemd5(data.local_file.platform_gc_notify_requirements.filename)
}

data "archive_file" "platform_gc_notify_tables" {
  type        = "zip"
  source_dir  = "${path.module}/etl/platform/gc_notify/tables"
  output_path = "${path.module}/etl/platform/gc_notify/tables.zip"
}

resource "aws_s3_object" "platform_gc_notify_tables" {
  bucket = var.glue_bucket_name
  key    = "platform/gc_notify/tables.zip"
  source = data.archive_file.platform_gc_notify_tables.output_path
  etag   = data.archive_file.platform_gc_notify_tables.output_md5
}

resource "aws_glue_job" "platform_gc_notify_job" {
  name = "Platform / GC Notify"

  glue_version           = "5.0"
  timeout                = 30 # minutes
  role_arn               = aws_iam_role.glue_etl.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name
  worker_type            = "G.2X"
  number_of_workers      = 2

  command {
    script_location = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_gc_notify_job.key}"
    python_version  = "3"
  }

  default_arguments = {
    "--continuous-log-logGroup"          = "/aws-glue/jobs/${aws_glue_security_configuration.encryption_at_rest.name}/service-role/${aws_iam_role.glue_etl.name}/output"
    "--continuous-log-logStreamPrefix"   = "platform_gc_notify"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-auto-scaling"              = "true"
    "--enable-job-insights"              = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--job-language"                     = "python"
    "--python-modules-installer-option"  = "-r"
    "--additional-python-modules"        = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_gc_notify_requirements.key}"
    "--source_bucket"                    = var.raw_bucket_name
    "--source_prefix"                    = "platform/gc-notify"
    "--transformed_bucket"               = var.transformed_bucket_name
    "--transformed_prefix"               = "platform/gc-notify"
    "--database_name_transformed"        = aws_glue_catalog_database.platform_gc_notify_production.name
    "--table_config_object"              = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_gc_notify_tables.key}"
    "--table_name_prefix"                = "platform_gc_notify"
    "--target_env"                       = var.env
  }
}

resource "aws_glue_trigger" "platform_gc_notify_job" {
  name     = "Platform / GC Notify"
  schedule = "cron(0 7 * * ? *)" # Daily at 7am UTC
  type     = "SCHEDULED"
  enabled  = local.is_production

  actions {
    job_name = aws_glue_job.platform_gc_notify_job.name
  }
}

#
# Platform / Support / Freshdesk
#
data "local_file" "platform_support_freshdesk_job" {
  filename = "${path.module}/etl/platform/support/freshdesk/process_tickets.py"
}

resource "aws_s3_object" "platform_support_freshdesk_job" {
  bucket = var.glue_bucket_name
  key    = "platform/support/freshdesk/process_tickets.py"
  source = data.local_file.platform_support_freshdesk_job.filename
  etag   = filemd5(data.local_file.platform_support_freshdesk_job.filename)
}

resource "aws_glue_job" "platform_support_freshdesk" {
  name = "Platform / Support / Freshdesk"

  glue_version           = "5.0"
  timeout                = 15 # minutes
  role_arn               = aws_iam_role.glue_etl.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name
  max_capacity           = 1

  command {
    script_location = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_support_freshdesk_job.key}"
    python_version  = "3.9"
    name            = "pythonshell"
  }

  default_arguments = {
    "--continuous-log-logGroup"          = "/aws-glue/python-jobs/${aws_glue_security_configuration.encryption_at_rest.name}/service-role/${aws_iam_role.glue_etl.name}/output"
    "--continuous-log-logStreamPrefix"   = "platform_support_freshdesk"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-auto-scaling"              = "true"
    "--enable-job-insights"              = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--job-language"                     = "python"
    "--source_bucket"                    = var.raw_bucket_name
    "--source_prefix"                    = "platform/support/freshdesk/"
    "--transformed_bucket"               = var.transformed_bucket_name
    "--transformed_prefix"               = "platform/support/freshdesk/"
    "--database_name_raw"                = aws_glue_catalog_database.platform_support_production_raw.name
    "--database_name_transformed"        = aws_glue_catalog_database.platform_support_production.name
    "--table_name"                       = "platform_support_freshdesk"
  }
}

resource "aws_glue_trigger" "platform_support_freshdesk" {
  name     = "Platform / Support / Freshdesk"
  schedule = "cron(00 7 * * ? *)" # 7am UTC every day
  type     = "SCHEDULED"
  enabled  = local.is_production

  actions {
    job_name = aws_glue_job.platform_support_freshdesk.name
  }
}

#
# BES / CRM / Salesforce
#
data "local_file" "bes_crm_salesforce_job" {
  filename = "${path.module}/etl/bes/crm/process_salesforce.py"
}

resource "aws_s3_object" "bes_crm_salesforce_job" {
  bucket = var.glue_bucket_name
  key    = "bes/crm/salesforce/process_salesforce.py"
  source = data.local_file.bes_crm_salesforce_job.filename
  etag   = filemd5(data.local_file.bes_crm_salesforce_job.filename)
}

resource "aws_glue_job" "bes_crm_salesforce" {
  name = "BES / CRM / Salesforce"

  glue_version           = "5.0"
  timeout                = 15 # minutes
  role_arn               = aws_iam_role.glue_etl.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name

  max_capacity = 0.0625

  command {
    script_location = "s3://${var.glue_bucket_name}/${aws_s3_object.bes_crm_salesforce_job.key}"
    python_version  = "3.9"
    name            = "pythonshell"
  }

  default_arguments = {
    "--continuous-log-logGroup"          = "/aws-glue/jobs/${aws_glue_security_configuration.encryption_at_rest.name}/service-role/${aws_iam_role.glue_etl.name}/output"
    "--continuous-log-logStreamPrefix"   = "bes_crm_salesforce"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-auto-scaling"              = "true"
    "--enable-job-insights"              = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--job-language"                     = "python"
    "--source_bucket"                    = var.raw_bucket_name
    "--source_prefix"                    = "bes/crm/salesforce/"
    "--transformed_bucket"               = var.transformed_bucket_name
    "--transformed_prefix"               = "bes/crm/salesforce/"
    "--database_name_transformed"        = aws_glue_catalog_database.bes_crm_salesforce_production.name
    "--table_name"                       = "account_opportunity"
  }
}

resource "aws_glue_trigger" "bes_crm_salesforce" {
  name     = "BES / CRM / Salesforce"
  schedule = "cron(00 7 * * ? *)" # 7am UTC every day
  type     = "SCHEDULED"
  enabled  = local.is_production

  actions {
    job_name = aws_glue_job.bes_crm_salesforce.name
  }
}
