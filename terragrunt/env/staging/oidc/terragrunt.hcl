include {
  path = find_in_parent_folders("root.hcl")
}

dependencies {
  paths = ["../buckets"]
}

dependency "buckets" {
  config_path                             = "../buckets"
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs = {
    raw_bucket_arn = "arn:aws:s3:::mock-raw-bucket"
  }
}

inputs = {
  raw_bucket_arn = dependency.buckets.outputs.raw_bucket_arn
}

terraform {
  source = "../../../aws//oidc"
}