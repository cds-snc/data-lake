#
# Holds exported data before transformation
#
module "raw_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v9.6.7"
  bucket_name       = "cds-data-lake-raw-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "raw/"
  }

  versioning = {
    enabled = true
  }
}

#
# ETL jobs process the `Raw` bucket and store the transformed data here
#
module "transformed_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v9.6.7"
  bucket_name       = "cds-data-lake-transformed-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "transformed/"
  }

  versioning = {
    enabled = true
  }
}

#
# Holds enriched data that has been created by combining multiple transformed datasets
#
module "curated_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v9.6.7"
  bucket_name       = "cds-data-lake-curated-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "curated/"
  }

  versioning = {
    enabled = true
  }
}

#
# Bucket access logs, stored for 30 days
#
module "log_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3_log_bucket?ref=v9.6.7"
  bucket_name       = "cds-data-lake-bucket-logs-${var.env}"
  versioning_status = "Enabled"

  lifecycle_rule = [{
    id      = "expire_logs"
    enabled = true
    expiration = {
      days                         = "30"
      expired_object_delete_marker = true
    }
    noncurrent_version_expiration = {
      days = "30"
    }
    abort_incomplete_multipart_upload = {
      days_after_initiation = "7"
    }
  }]

  billing_tag_value = var.billing_tag_value
}