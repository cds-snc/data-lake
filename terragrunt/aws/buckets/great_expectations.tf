module "gx_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v10.4.6"
  bucket_name       = "cds-data-lake-gx-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "gx/"
  }

  lifecycle_rule = [
    local.lifecycle_remove_noncurrent_versions,
    local.lifecycle_transition_storage
  ]

  versioning = {
    enabled = true
  }
}

# S3 bucket website configuration
resource "aws_s3_bucket_website_configuration" "gx_bucket_website" {
  bucket = module.gx_bucket.s3_bucket_id

  index_document {
    suffix = "index.html"
  }
}

# S3 bucket policy to allow public read for website hosting
resource "aws_s3_bucket_policy" "gx_bucket_public_read" {
  bucket = module.gx_bucket.s3_bucket_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = "${module.gx_bucket.s3_bucket_arn}/*"
      }
    ]
  })
}

resource "aws_cloudfront_distribution" "gx_bucket_cdn" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name = aws_s3_bucket_website_configuration.gx_bucket_website.website_endpoint
    origin_id   = "gx-bucket-website-origin"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "gx-bucket-website-origin"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}

output "gx_bucket_website_url" {
  value = aws_cloudfront_distribution.gx_bucket_cdn.domain_name
}