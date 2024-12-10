locals {
  vars = read_terragrunt_config("../env_vars.hcl")
}

inputs = {
  account_id             = "${local.vars.inputs.account_id}"
  billing_tag_value      = "${local.vars.inputs.billing_tag_value}"
  env                    = "${local.vars.inputs.env}"
  region                 = "ca-central-1"
  superset_iam_role_arns = [
    "arn:aws:iam::066023111852:role/SupersetAthenaRead",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead"
  ]
}

remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    encrypt        = true
    bucket         = "cds-data-lake-tfstate-${local.vars.inputs.env}"
    dynamodb_table = "terraform-state-lock-dynamo"
    region         = "ca-central-1"
    key            = "${path_relative_to_include()}/terraform.tfstate"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = file("./common/provider.tf")
}

generate "common_variables" {
  path      = "common_variables.tf"
  if_exists = "overwrite"
  contents  = file("./common/common_variables.tf")
}
