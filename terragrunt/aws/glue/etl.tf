#
# Platform / GC Forms / Generate test data
#
data "local_file" "forms_generate_test_data" {
  filename = "${path.module}/etl/platform/gc-forms/scripts/generate_test_data.py"
}

resource "aws_s3_object" "forms_generate_test_data" {
  bucket = var.glue_bucket_name
  key    = "platform/gc-forms/generate_test_data.py"
  source = data.local_file.forms_generate_test_data.filename
  etag   = filemd5(data.local_file.forms_generate_test_data.filename)
}

resource "aws_glue_job" "forms_generate_test_data" {
  name = "Platform / GC Forms / Generate test data"

  timeout                = 15 # minutes
  role_arn               = aws_iam_role.glue_etl.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name

  command {
    script_location = "s3://${var.glue_bucket_name}/${aws_s3_object.forms_generate_test_data.key}"
    python_version  = "3"
  }

  default_arguments = {
    "--continuous-log-logGroup"          = "/aws-glue/jobs/${aws_glue_security_configuration.encryption_at_rest.name}/service-role/${aws_iam_role.glue_etl.name}/output"
    "--continuous-log-logStreamPrefix"   = "forms_generate_test_data"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--output_s3_path"                   = "s3://${var.transformed_bucket_name}/platform/gc-forms/forms/test/"
    "--num_partitions"                   = "1"
  }
}

#
# Platform / Support / Freshdesk
#
data "local_file" "platform_support_freshdesk_job" {
  filename = "${path.module}/etl/platform/support/freshdesk/scripts/process_tickets.py"
}

data "local_file" "platform_support_freshdesk_requirements" {
  filename = "${path.module}/etl/platform/support/freshdesk/scripts/requirements.txt"
}

resource "aws_s3_object" "platform_support_freshdesk_job" {
  bucket = var.glue_bucket_name
  key    = "platform/support/freshdesk/process_tickets.py"
  source = data.local_file.platform_support_freshdesk_job.filename
  etag   = filemd5(data.local_file.platform_support_freshdesk_job.filename)
}

resource "aws_s3_object" "platform_support_freshdesk_requirements" {
  bucket = var.glue_bucket_name
  key    = "platform/support/freshdesk/requirements.txt"
  source = data.local_file.platform_support_freshdesk_requirements.filename
  etag   = filemd5(data.local_file.platform_support_freshdesk_requirements.filename)
}

resource "aws_glue_job" "platform_support_freshdesk" {
  name = "Platform / Support / Freshdesk"

  glue_version           = "5.0"
  timeout                = 15 # minutes
  role_arn               = aws_iam_role.glue_etl.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name
  execution_class        = "FLEX"

  command {
    script_location = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_support_freshdesk_job.key}"
    python_version  = "3"
  }

  default_arguments = {
    "--continuous-log-logGroup"          = "/aws-glue/jobs/${aws_glue_security_configuration.encryption_at_rest.name}/service-role/${aws_iam_role.glue_etl.name}/output"
    "--continuous-log-logStreamPrefix"   = "platform_support_freshdesk"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-auto-scaling"              = "true"
    "--enable-job-insights"              = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--job-language"                     = "python"
    "--python-modules-installer-option"  = "-r"
    "--additional-python-modules"        = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_support_freshdesk_requirements.key}"
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

  actions {
    job_name = aws_glue_job.platform_support_freshdesk.name
  }
}

#
# BES / CRM / Salesforce
#
data "local_file" "bes_crm_salesforce_job" {
  filename = "${path.module}/etl/bes/crm/scripts/process_salesforce.py"
}

data "local_file" "bes_crm_salesforce_requirements" {
  filename = "${path.module}/etl/bes/crm/scripts/requirements.txt"
}

resource "aws_s3_object" "bes_crm_salesforce_job" {
  bucket = var.glue_bucket_name
  key    = "bes/crm/salesforce/process_salesforce.py"
  source = data.local_file.bes_crm_salesforce_job.filename
  etag   = filemd5(data.local_file.bes_crm_salesforce_job.filename)
}

resource "aws_s3_object" "bes_crm_salesforce_requirements" {
  bucket = var.glue_bucket_name
  key    = "bes/crm/salesforce/requirements.txt"
  source = data.local_file.bes_crm_salesforce_requirements.filename
  etag   = filemd5(data.local_file.bes_crm_salesforce_requirements.filename)
}

resource "aws_glue_job" "bes_crm_salesforce" {
  name = "BES / CRM / Salesforce"

  glue_version           = "5.0"
  timeout                = 15 # minutes
  role_arn               = aws_iam_role.glue_etl.arn
  max_capacity           = 0.0625

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

  actions {
    job_name = aws_glue_job.bes_crm_salesforce.name
  }
}