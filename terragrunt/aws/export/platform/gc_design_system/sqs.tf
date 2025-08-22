#
# SQS infrastructure for GC Design System CloudFront log processing
#

# SQS Queue for CloudFront log file events
resource "aws_sqs_queue" "cloudfront_processing_queue" {
  name = local.gc_design_system_cloudfront_queue_name

  # Standard message retention (14 days)
  message_retention_seconds = 1209600

  # Visibility timeout
  visibility_timeout_seconds = 960 # 16 minutes (should be longer than 15min lambda timeout)

  # Encryption
  kms_master_key_id = aws_kms_key.gc_design_system_exports.arn

  tags = {
    Billing = var.billing_tag_value
  }
}

# Dead letter queue for failed messages
resource "aws_sqs_queue" "cloudfront_processing_dlq" {
  name = "${local.gc_design_system_cloudfront_queue_name}-dlq"

  # Encryption
  kms_master_key_id = aws_kms_key.gc_design_system_exports.arn

  tags = {
    Billing = var.billing_tag_value
  }
}

# Redrive policy for main queue
resource "aws_sqs_queue_redrive_policy" "cloudfront_processing_queue_redrive" {
  queue_url = aws_sqs_queue.cloudfront_processing_queue.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.cloudfront_processing_dlq.arn
    maxReceiveCount     = 3
  })
}

# S3 bucket notification to send events to SQS
resource "aws_s3_bucket_notification" "cloudfront_trigger" {
  bucket = var.raw_bucket_name

  queue {
    queue_arn     = aws_sqs_queue.cloudfront_processing_queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "platform/gc-design-system/cloudfront-logs/"
    filter_suffix = ".gz"
  }

  depends_on = [
    aws_sqs_queue_policy.cloudfront_s3_events,
    aws_sqs_queue.cloudfront_processing_queue
  ]
}

# SQS queue policy to allow S3 to send messages
resource "aws_sqs_queue_policy" "cloudfront_s3_events" {
  queue_url = aws_sqs_queue.cloudfront_processing_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3ToSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.cloudfront_processing_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = var.raw_bucket_arn
          }
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}
