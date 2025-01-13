terraform {
  source = "../../../aws//export"
}

dependencies {
  paths = ["../buckets"]
}

dependency "buckets" {
  config_path                             = "../buckets"
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs = {
    raw_bucket_arn  = "arn:aws:s3:::mock-raw-bucket"
    raw_bucket_name = "mock-raw-bucket"
  }
}

inputs = {
  raw_bucket_arn  = dependency.buckets.outputs.raw_bucket_arn
  raw_bucket_name = dependency.buckets.outputs.raw_bucket_name
}

include {
  path = find_in_parent_folders()
}
