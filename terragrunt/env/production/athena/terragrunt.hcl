terraform {
  source = "../../../aws//athena"
}

dependencies {
  paths = ["../buckets"]
}

dependency "buckets" {
  config_path                             = "../buckets"
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs = {
    athena_bucket_arn  = "arn:aws:s3:::mock-athena-bucket"
    athena_bucket_name = "mock-athena-bucket"
  }
}

inputs = {
  athena_bucket_arn  = dependency.buckets.outputs.athena_bucket_arn
  athena_bucket_name = dependency.buckets.outputs.athena_bucket_name
}

include {
  path = find_in_parent_folders()
}
