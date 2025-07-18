#
# Holds Athena query resuts
#
module "athena_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v10.6.2"
  bucket_name       = "cds-data-lake-athena-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "athena/"
  }

  lifecycle_rule = [
    local.lifecycle_expire_all,
    local.lifecycle_remove_noncurrent_versions
  ]

  versioning = {
    enabled = true
  }
}

resource "aws_s3_bucket_policy" "athena_bucket" {
  bucket = module.athena_bucket.s3_bucket_id
  policy = data.aws_iam_policy_document.athena_bucket.json
}

data "aws_iam_policy_document" "athena_bucket" {
  statement {
    sid    = "SupersetReadWrite"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = var.superset_iam_role_arns
    }
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:PutObject"
    ]
    resources = [
      module.athena_bucket.s3_bucket_arn,
      "${module.athena_bucket.s3_bucket_arn}/*"
    ]
  }
}