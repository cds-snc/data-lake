#
# Holds exported data before transformation
#
module "raw_bucket" {
  source            = "github.com/cds-snc/terraform-modules//S3?ref=v10.4.2"
  bucket_name       = "cds-data-lake-raw-${var.env}"
  billing_tag_value = var.billing_tag_value

  logging = {
    target_bucket = module.log_bucket.s3_bucket_id
    target_prefix = "raw/"
  }

  lifecycle_rule = [
    local.lifecycle_remove_noncurrent_versions,
    local.lifecycle_transition_storage,
    local.lifecycle_expire_gc_notify
  ]

  versioning = {
    enabled = true
  }
}

resource "aws_s3_bucket_policy" "raw_bucket" {
  bucket = module.raw_bucket.s3_bucket_id
  policy = data.aws_iam_policy_document.raw_bucket.json
}

#
# There is a 20kb limit on the size of the policy document
#
data "aws_iam_policy_document" "raw_bucket" {
  statement {
    sid    = "ReplicateToBucket"
    effect = "Allow"
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::563894450011:role/SalesforceReplicateToDataLake",
        "arn:aws:iam::659087519042:role/BillingExtractTags",
        "arn:aws:iam::659087519042:role/CostUsageReplicateToDataLake",
        "arn:aws:iam::957818836222:role/FormsS3ReplicatePlatformDataLake",
      ]
    }
    actions = [
      "s3:List*",
      "s3:GetBucketVersioning",
      "s3:PutBucketVersioning",
      "s3:PutObject",
      "s3:ReplicateObject",
      "s3:ReplicateDelete"
    ]
    resources = [
      module.raw_bucket.s3_bucket_arn,
      "${module.raw_bucket.s3_bucket_arn}/*"
    ]
  }

  statement {
    sid    = "RDSExportToBucket"
    effect = "Allow"
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::296255494825:role/NotifyExportToPlatformDataLake",
      ]
    }
    actions = [
      "s3:PutObject*",
      "s3:ListBucket",
      "s3:GetObject*",
      "s3:DeleteObject*",
      "s3:GetBucketLocation"
    ]
    resources = [
      module.raw_bucket.s3_bucket_arn,
      "${module.raw_bucket.s3_bucket_arn}/*"
    ]
  }
}
