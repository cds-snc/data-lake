locals {
  data_lake_github_data_export = "data-lake-github-data-export"
  data_lake_docker_push        = "data-lake-docker-push"
}

#
# Create the OIDC roles used by the GitHub workflows
# The roles can be assumed by the GitHub workflows according to the `claim`
# attribute of each role.
# 
module "github_workflow_roles" {
  count = var.env == "production" ? 1 : 0

  source            = "github.com/cds-snc/terraform-modules//gh_oidc_role?ref=v10.11.4"
  billing_tag_value = var.billing_tag_value
  roles = [
    {
      name      = local.data_lake_github_data_export
      repo_name = "*" # Allow any CDS repo to use this role
      claim     = "ref:refs/heads/main"
    }
  ]
}

#
# Attach polices to the OIDC roles to grant them permissions.  These
# attachments are scoped to only the environments that require the role.
#

#
# Allow GitHub workflows in CDS repos to export data to the Raw S3 bucket
#
resource "aws_iam_role_policy_attachment" "data_lake_github_data_export" {
  count = var.env == "production" ? 1 : 0

  role       = local.data_lake_github_data_export
  policy_arn = resource.aws_iam_policy.data_lake_github_data_export[0].arn
  depends_on = [
    module.github_workflow_roles[0]
  ]
}

resource "aws_iam_policy" "data_lake_github_data_export" {
  count = var.env == "production" ? 1 : 0

  name   = local.data_lake_github_data_export
  path   = "/service-role/"
  policy = data.aws_iam_policy_document.s3_read_write_raw_github.json
}

data "aws_iam_policy_document" "s3_read_write_raw_github" {
  statement {
    sid = "ReadWriteRawGitHubS3Bucket"
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${var.raw_bucket_arn}/operations/github/*"
    ]
  }
}

#
# Allow GitHub workflows in the data-lake repo to push Docker images to ECR
# and update Lambda function code.  This role is scoped to only the permissions
# needed by the Docker build, push and deploy workflows.
#
module "docker_push_role" {
  source            = "github.com/cds-snc/terraform-modules//gh_oidc_role?ref=v10.11.4"
  billing_tag_value = var.billing_tag_value
  roles = [
    {
      name      = local.data_lake_docker_push
      repo_name = "data-lake"
      claim     = "ref:refs/heads/main"
    }
  ]
}

resource "aws_iam_role_policy_attachment" "data_lake_docker_push_ecr" {
  role       = local.data_lake_docker_push
  policy_arn = aws_iam_policy.data_lake_docker_push_ecr.arn
  depends_on = [module.docker_push_role]
}

resource "aws_iam_role_policy_attachment" "data_lake_docker_push_lambda" {
  role       = local.data_lake_docker_push
  policy_arn = aws_iam_policy.data_lake_docker_push_lambda.arn
  depends_on = [module.docker_push_role]
}

resource "aws_iam_policy" "data_lake_docker_push_ecr" {
  name   = "${local.data_lake_docker_push}-ecr"
  path   = "/service-role/"
  policy = data.aws_iam_policy_document.data_lake_docker_push_ecr.json
}

resource "aws_iam_policy" "data_lake_docker_push_lambda" {
  name   = "${local.data_lake_docker_push}-lambda"
  path   = "/service-role/"
  policy = data.aws_iam_policy_document.data_lake_docker_push_lambda.json
}

data "aws_iam_policy_document" "data_lake_docker_push_ecr" {
  statement {
    sid = "ECRGetAuthorizationToken"
    actions = [
      "ecr:GetAuthorizationToken",
    ]
    resources = ["*"]
  }

  statement {
    sid = "ECRPushImages"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [
      "arn:aws:ecr:${var.region}:${var.account_id}:repository/*-export",
    ]
  }
}

data "aws_iam_policy_document" "data_lake_docker_push_lambda" {
  statement {
    sid = "LambdaUpdateFunctionCode"
    actions = [
      "lambda:GetFunction",
      "lambda:UpdateFunctionCode",
    ]
    resources = [
      "arn:aws:lambda:${var.region}:${var.account_id}:function:*-export",
    ]
  }
}