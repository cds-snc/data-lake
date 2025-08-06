#
# Glue Crawler for GC Design System Airtable data
#

# Security Configuration for Glue Crawler
resource "aws_glue_security_configuration" "platform_gc_design_system" {
  name = "platform-gc-design-system-encryption"

  encryption_configuration {
    cloudwatch_encryption {
      cloudwatch_encryption_mode = "SSE-KMS"
      kms_key_arn                = aws_kms_key.platform_gc_design_system.arn
    }

    job_bookmarks_encryption {
      job_bookmarks_encryption_mode = "CSE-KMS"
      kms_key_arn                   = aws_kms_key.platform_gc_design_system.arn
    }

    s3_encryption {
      s3_encryption_mode = "SSE-S3"
    }
  }
}

resource "aws_glue_crawler" "platform_gc_design_system_airtable" {
  name                   = local.gc_design_system_crawler_name
  role                   = aws_iam_role.glue_crawler_role.arn
  database_name          = "platform_gc_design_system"
  security_configuration = aws_glue_security_configuration.platform_gc_design_system.name

  s3_target {
    path = "s3://${var.transformed_bucket_name}/${local.gc_design_system_export_path}/"
  }

  table_prefix = "platform_gc_design_system_"

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DELETE_FROM_DATABASE"
  }

  configuration = jsonencode({
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
      Tables = {
        AddOrUpdateBehavior = "MergeNewColumns"
      }
    }
    Version = 1
  })

  tags = {
    CostCentre = var.billing_tag_value
  }
}

# Glue Database
resource "aws_glue_catalog_database" "platform_gc_design_system" {
  name        = "platform_gc_design_system"
  description = "Database for GC Design System data from Airtable"
}

# IAM Role for Glue Crawler
resource "aws_iam_role" "glue_crawler_role" {
  name = "platform-gc-design-system-glue-crawler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    CostCentre = var.billing_tag_value
  }
}

# IAM Policy for Glue Crawler
resource "aws_iam_role_policy" "glue_crawler_policy" {
  name = "platform-gc-design-system-glue-crawler-policy"
  role = aws_iam_role.glue_crawler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetTables",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:GetPartitions",
          "glue:CreatePartition",
          "glue:UpdatePartition",
          "glue:DeletePartition"
        ]
        Resource = [
          "arn:aws:glue:*:*:catalog",
          "arn:aws:glue:*:*:database/platform_gc_design_system",
          "arn:aws:glue:*:*:table/platform_gc_design_system/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${var.transformed_bucket_arn}",
          "${var.transformed_bucket_arn}/${local.gc_design_system_export_path}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws-glue/crawlers*"
      }
    ]
  })
}

# Attach AWS managed policy for Glue service role
resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue_crawler_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}
