terraform {
  source = "../../../aws//alarms"
}

dependencies {
  paths = ["../glue"]
}

dependency "glue" {
  config_path                             = "../glue"
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs = {
    glue_crawler_log_group_name = "mock-glue-crawler-log-group"
  }
}

inputs = {
  glue_crawler_log_group_name = dependency.glue.outputs.glue_crawler_log_group_name
}

include {
  path = find_in_parent_folders()
}
