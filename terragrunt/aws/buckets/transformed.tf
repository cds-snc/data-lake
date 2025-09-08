#
# ETL jobs process the `Raw` bucket and store the transformed data here
#
module "transformed_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v10.7.0"
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

resource "aws_s3_bucket_policy" "transformed_bucket" {
  bucket = module.transformed_bucket.s3_bucket_id
  policy = data.aws_iam_policy_document.transformed_bucket.json
}

data "aws_iam_policy_document" "transformed_bucket" {
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
      module.transformed_bucket.s3_bucket_arn,
      "${module.transformed_bucket.s3_bucket_arn}/*"
    ]
  }
}
