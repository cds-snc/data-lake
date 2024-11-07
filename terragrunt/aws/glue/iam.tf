#
# Glue crawler role
#
resource "aws_iam_role" "glue_crawler" {
  name               = "AWSGlueCrawler-DataLake"
  assume_role_policy = data.aws_iam_policy_document.glue_crawler_assume.json
  path               = "/service-role/"
}

data "aws_iam_policy_document" "glue_crawler_assume" {
  statement {
    actions = [
      "sts:AssumeRole",
    ]
    principals {
      type = "Service"
      identifiers = [
        "glue.amazonaws.com",
      ]
    }
  }
}

resource "aws_iam_role_policy_attachment" "aws_glue_service_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
  role       = aws_iam_role.glue_crawler.name
}

resource "aws_iam_policy" "glue_crawler" {
  name        = "AWSGlueCrawler-DataLake"
  policy      = data.aws_iam_policy_document.glue_s3_crawler.json
  description = "This policy will be used by the AWS Glue Crawler."
  path        = "/service-role/"
}

resource "aws_iam_role_policy_attachment" "glue_crawler" {
  policy_arn = aws_iam_policy.glue_s3_crawler.arn
  role       = aws_iam_role.glue_s3_crawler.name
}

data "aws_iam_policy_document" "glue_crawler" {
  statement {
    sid = "ReadDataLakeS3Buckets"
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${var.curated_bucket_arn}/*",
      "${var.raw_bucket_arn}/*",
      "${var.transformed_bucket_arn}/*"
    ]
  }
}
