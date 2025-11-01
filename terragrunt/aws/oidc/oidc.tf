locals {
  data_lake_release            = "data-lake-release"
  data_lake_github_data_export = "data-lake-github-data-export"
}

#
# Create the OIDC roles used by the GitHub workflows
# The roles can be assumed by the GitHub workflows according to the `claim`
# attribute of each role.
# 
module "github_workflow_roles" {
  count = var.env == "production" ? 1 : 0

  source            = "github.com/cds-snc/terraform-modules//gh_oidc_role?ref=v10.8.3"
  billing_tag_value = var.billing_tag_value
  roles = [
    {
      name      = local.data_lake_release
      repo_name = "data-lake"
      claim     = "ref:refs/tags/v*" # Version tags prefixed with v
    },
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
# Runs after a new GitHub release is created to update Prod infrastructure
#
resource "aws_iam_role_policy_attachment" "data_lake_release" {
  count = var.env == "production" ? 1 : 0

  role       = local.data_lake_release
  policy_arn = data.aws_iam_policy.admin.arn
  depends_on = [
    module.github_workflow_roles[0]
  ]
}

data "aws_iam_policy" "admin" {
  # checkov:skip=CKV_AWS_275:This policy is required for the Terraform apply
  name = "AdministratorAccess"
}
