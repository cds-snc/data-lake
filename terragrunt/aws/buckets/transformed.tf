#
# ETL jobs process the `Raw` bucket and store the transformed data here
#
module "transformed_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v9.6.8"
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
