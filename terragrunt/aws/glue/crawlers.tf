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
# Platform / GC Forms / Forms
#
resource "aws_glue_crawler" "platform_gc_forms_templates_production_raw" {
  name          = "Platform / GC Forms / Templates"
  description   = "Classify the raw GC Forms template data"
  database_name = aws_glue_catalog_database.platform_gc_forms_production_raw.name
  table_prefix  = "platform_gc_forms_raw_"

  role                   = aws_iam_role.glue_crawler.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name

  s3_target {
    path = "s3://${var.raw_bucket_name}/platform/gc-forms"
  }

  configuration = jsonencode(
    {
      CrawlerOutput = {
        Tables = {
          TableThreshold = 5
        }
      }
      CreatePartitionIndex = true
      Version              = 1
  })
}

#
# Platform / Support / Freshdesk
#
resource "aws_glue_crawler" "platform_support_freshdesk_production" {
  name          = "Platform / Support / Freshdesk"
  description   = "Classify the Platform Freshdesk support ticket data"
  database_name = aws_glue_catalog_database.platform_support_production_raw.name
  table_prefix  = "platform_support_"
  classifiers   = [aws_glue_classifier.json_object_array.name]

  role                   = aws_iam_role.glue_crawler.arn
  security_configuration = aws_glue_security_configuration.encryption_at_rest.name

  s3_target {
    path = "s3://${var.raw_bucket_name}/platform/support/freshdesk"
  }

  configuration = jsonencode(
    {
      CrawlerOutput = {
        Tables = {
          TableThreshold = 1
        }
      }
      Grouping = {
        TableGroupingPolicy = "CombineCompatibleSchemas"
      }
      CreatePartitionIndex = true
      Version              = 1
  })

  # 6am UTC check for schema changes on the first 10 days of each month
  schedule = local.is_production ? "cron(00 6 1-10 * ? *)" : null
}

#
# Operations / AWS / Cost and Usage Report
#
resource "aws_glue_crawler" "operations_aws_production_cost_usage_report" {
  name          = "Operations / AWS / Cost and Usage Report"
  description   = "Classify the AWS Organization Cost and Usage Report data"
  database_name = aws_glue_catalog_database.operations_aws_production_raw.name
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

  # Run for the first 10 days of each month to create the new partition key
  schedule = local.is_production ? "cron(00 7 1-10 * ? *)" : null
}

#
# Operations / AWS / Organization / Account Tags
#
resource "aws_glue_crawler" "operations_aws_production_account_tags" {
  name          = "Operations / AWS / Organization / Account Tags"
  description   = "Classify the AWS Organization account tag extract"
  database_name = aws_glue_catalog_database.operations_aws_production_raw.name
  table_prefix  = "account_tags_"
  classifiers   = [aws_glue_classifier.json_object_array.name]

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

  # Check for schema changes each month
  schedule = local.is_production ? "cron(00 7 1 * ? *)" : null
}

# JSON classifier for arrays of objects
resource "aws_glue_classifier" "json_object_array" {
  name = "json_object_array"

  json_classifier {
    json_path = "$[*]"
  }
}
