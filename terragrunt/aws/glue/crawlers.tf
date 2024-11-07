resource "aws_glue_security_configuration" "encryption_at_rest" {
  name = "encryption-at-rest"

  encryption_configuration {
    cloudwatch_encryption {
      cloudwatch_encryption_mode = "SSE-KMS"
      kms_key_arn                = aws_kms_key.aws_glue.arn
    }

    job_bookmarks_encryption {
      job_bookmarks_encryption_mode = "CSE-KMS"
      kms_key_arn                   = aws_kms_key.aws_glue.arn
    }

    s3_encryption {
      s3_encryption_mode = "SSE-S3"
    }
  }
}

#
# Cost and Usage Report
#
resource "aws_glue_crawler" "operations_aws_production_cost_usage_report" {
  name          = "Cost and Usage Report 2.0"
  database_name = aws_glue_catalog_database.operations_aws_production.name
  table_prefix  = "cost_usage_report_"

  role                   = aws_iam_role.glue_crawler.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name

  s3_target {
    path = "s3://${var.raw_bucket_name}/operations/aws/cost-usage-report"
  }

  configuration = jsonencode(
    {
      CrawlerOutput = {
        Tables = {
          TableThreshold = 2
        }
      }
      CreatePartitionIndex = true
      Version              = 1
  })

  # TODO: enable schedule once job has been tested
  # schedule = "cron(00 7 1 * ? *)" # Create the new month's partition key
}

#
# Organization Account Tags
#
resource "aws_glue_crawler" "operations_aws_production_account_tags" {
  name          = "Organization Account Tags"
  database_name = aws_glue_catalog_database.operations_aws_production.name
  table_prefix  = "org_"

  role                   = aws_iam_role.glue_crawler.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name

  s3_target {
    path = "s3://${var.raw_bucket_name}/operations/aws/organization"
  }

  configuration = jsonencode(
    {
      CrawlerOutput = {
        Tables = {
          TableThreshold = 1
        }
      }
      CreatePartitionIndex = true
      Version              = 1
  })

  # TODO: enable schedule once job has been tested
  # schedule = "cron(00 13 * * ? *)" # Pickup new accounts each day
}
