locals {
  data_lake_release = "data-lake-release"
}

#
# Create the OIDC roles used by the GitHub workflows
# The roles can be assumed by the GitHub workflows according to the `claim`
# attribute of each role.
# 
module "github_workflow_roles" {
  count = var.env == "production" ? 1 : 0

  source            = "github.com/cds-snc/terraform-modules//gh_oidc_role?ref=v10.4.6"
  billing_tag_value = var.billing_tag_value
  roles = [
    {
      name      = local.data_lake_release
      repo_name = "data-lake"
      claim     = "ref:refs/tags/v*" # Version tags prefixed with v
    }
  ]
}

#
# Attach polices to the OIDC roles to grant them permissions.  These
# attachments are scoped to only the environments that require the role.
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
