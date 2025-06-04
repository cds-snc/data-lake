resource "aws_athena_workgroup" "data_lake" {
  name = "data-lake-${var.env}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.athena_bucket_name}/data-lake/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}

resource "aws_athena_named_query" "notify_enriched" {
  name        = "notify_enriched"
  database    = "platform_gc_notify_${var.env}"
  query       = templatefile("${path.module}/queries/notify_enriched.sql.tmpl", {
    curated_bucket = var.curated_bucket_name
  })
  description = "Enriched notifications query"
  workgroup   = aws_athena_workgroup.data_lake.name
}