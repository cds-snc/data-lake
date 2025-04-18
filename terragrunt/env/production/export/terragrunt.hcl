terraform {
  source = "../../../aws//export"
}

dependencies {
  paths = ["../buckets", "../alarms"]
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

dependency "alarms" {
  config_path                             = "../alarms"
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs = {
    sns_topic_alarm_action_arn = "arn:aws:sns:ca-central-1:123456789012:mock-alarm-topic"
    sns_topic_ok_action_arn    = "arn:aws:sns:ca-central-1:123456789012:mock-ok-topic"
  }
}

inputs = {
  raw_bucket_arn  = dependency.buckets.outputs.raw_bucket_arn
  raw_bucket_name = dependency.buckets.outputs.raw_bucket_name

  sns_topic_alarm_action_arn = dependency.alarms.outputs.sns_topic_alarm_action_arn
  sns_topic_ok_action_arn    = dependency.alarms.outputs.sns_topic_ok_action_arn
}

include {
  path = find_in_parent_folders("root.hcl")
}
