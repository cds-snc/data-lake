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
# Platform / Support / Generate test data
#
data "local_file" "platform_support_freshdesk" {
  filename = "${path.module}/etl/platform/support/freshdesk/scripts/process_tickets.py"
}

resource "aws_s3_object" "platform_support_freshdesk" {
  bucket = var.glue_bucket_name
  key    = "platform/support/freshdesk/process_tickets.py"
  source = data.local_file.platform_support_freshdesk.filename
  etag   = filemd5(data.local_file.platform_support_freshdesk.filename)
}

resource "aws_glue_job" "platform_support_freshdesk" {
  name = "Platform / Support / Freshdesk"

  timeout                = 15 # minutes
  role_arn               = aws_iam_role.glue_etl.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name

  command {
    script_location = "s3://${var.glue_bucket_name}/${aws_s3_object.platform_support_freshdesk.key}"
    python_version  = "3"
  }

  default_arguments = {
    "--continuous-log-logGroup"          = "/aws-glue/jobs/${aws_glue_security_configuration.encryption_at_rest.name}/service-role/${aws_iam_role.glue_etl.name}/output"
    "--continuous-log-logStreamPrefix"   = "platform_support_freshdesk"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--additional-python-modules"        = "awswrangler==3.11.0"
    "--source_bucket"                    = var.raw_bucket_name
    "--source_prefix"                    = "platform/support/freshdesk/"
    "--transformed_bucket"               = var.transformed_bucket_name
    "--transformed_prefix"               = "platform/support/freshdesk/"
    "--database_name_raw"                = aws_glue_catalog_database.platform_support_production_raw.name
    "--database_name_transformed"        = aws_glue_catalog_database.platform_support_production.name
    "--table_name"                       = "platform_support_freshdesk"
  }
}
