#
# Holds exported data before transformation
#
module "raw_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=4768da635c66d3333538835b215887cb3c7e3036"
  bucket_name       = "cds-data-lake-raw-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "raw/"
  }

  lifecycle_rule = [
    local.lifecycle_remove_noncurrent_versions,
    local.lifecycle_transition_storage
  ]

  versioning = {
    enabled = true
  }
}

#
# ETL jobs process the `Raw` bucket and store the transformed data here
#
module "transformed_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=4768da635c66d3333538835b215887cb3c7e3036"
  bucket_name       = "cds-data-lake-transformed-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "transformed/"
  }

  lifecycle_rule = [
    local.lifecycle_remove_noncurrent_versions
  ]

  versioning = {
    enabled = true
  }
}

#
# Holds enriched data that has been created by combining multiple transformed datasets
#
module "curated_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=4768da635c66d3333538835b215887cb3c7e3036"
  bucket_name       = "cds-data-lake-curated-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "curated/"
  }

  lifecycle_rule = [
    local.lifecycle_remove_noncurrent_versions
  ]

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

  lifecycle_rule = [
    local.lifecycle_expire_all,
    local.lifecycle_remove_noncurrent_versions
  ]

  billing_tag_value = var.billing_tag_value
}