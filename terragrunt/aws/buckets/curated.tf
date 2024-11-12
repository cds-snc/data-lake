#
# Holds enriched data that has been created by combining multiple transformed datasets
#
module "curated_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v10.0.0"
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
