#
# Holds ETL job scripts used by Glue
#
module "glue_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v10.5.2"
  bucket_name       = "cds-data-lake-glue-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "glue/"
  }

  lifecycle_rule = [
    local.lifecycle_remove_noncurrent_versions
  ]

  versioning = {
    enabled = true
  }
}
