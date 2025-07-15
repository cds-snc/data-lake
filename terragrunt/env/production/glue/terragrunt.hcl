terraform {
  source = "../../../aws//glue"
}

dependencies {
  paths = ["../buckets"]
}

dependency "buckets" {
  config_path                             = "../buckets"
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs = {
    athena_bucket_arn      = "arn:aws:s3:::mock-athena-bucket"
    athena_bucket_name     = "mock-athena-bucket"
    glue_bucket_arn         = "arn:aws:s3:::mock-glue-bucket"
    glue_bucket_name        = "mock-glue-bucket"
    raw_bucket_arn          = "arn:aws:s3:::mock-raw-bucket"
    raw_bucket_name         = "mock-raw-bucket"
    transformed_bucket_arn  = "arn:aws:s3:::mock-transformed-bucket"
    transformed_bucket_name = "mock-transformed-bucket"
  }
}

inputs = {
  athena_bucket_arn       = dependency.buckets.outputs.athena_bucket_arn
  athena_bucket_name      = dependency.buckets.outputs.athena_bucket_name
  glue_bucket_arn         = dependency.buckets.outputs.glue_bucket_arn
  glue_bucket_name        = dependency.buckets.outputs.glue_bucket_name
  raw_bucket_arn          = dependency.buckets.outputs.raw_bucket_arn
  raw_bucket_name         = dependency.buckets.outputs.raw_bucket_name
  transformed_bucket_arn  = dependency.buckets.outputs.transformed_bucket_arn
  transformed_bucket_name = dependency.buckets.outputs.transformed_bucket_name
}

include {
  path = find_in_parent_folders("root.hcl")
}
