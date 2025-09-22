#
# Holds enriched data that has been created by combining multiple transformed datasets
#
module "curated_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v10.8.0"
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

resource "aws_s3_bucket_policy" "curated_bucket" {
  bucket = module.curated_bucket.s3_bucket_id
  policy = data.aws_iam_policy_document.curated_bucket.json
}

data "aws_iam_policy_document" "curated_bucket" {
  statement {
    sid    = "SupersetRead"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = var.superset_iam_role_arns
    }
    actions = [
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      module.curated_bucket.s3_bucket_arn,
      "${module.curated_bucket.s3_bucket_arn}/*"
    ]
  }
}