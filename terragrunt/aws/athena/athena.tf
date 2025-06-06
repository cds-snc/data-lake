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

resource "aws_athena_workgroup" "data_lake_curated" {
  name = "data-lake-curated-${var.env}"

  configuration {
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.curated_bucket_name}/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}