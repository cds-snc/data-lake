terraform {
  source = "../../../aws//stepfunctions"
}

dependencies {
  paths = ["../glue", "../buckets"]
}


dependency "buckets" {
  config_path                             = "../buckets"
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs = {
    curated_bucket_name     = "mock-curated-bucket"
    athena_bucket_name       = "mock-athena-bucket"
    transformed_bucket_name  = "mock-transformed-bucket"
  }
}

dependency "glue" {
  config_path                             = "../glue"
  mock_outputs_merge_strategy_with_state  = "shallow"
  mock_outputs_allowed_terraform_commands = ["init", "fmt", "validate", "plan", "show"]
  mock_outputs = {
    platform_gc_forms_job_name      = "Gc Forms Glue Job"
    platform_gc_notify_job_name     = "Gc Notify Glue Job"
    platform_support_freshdesk_name = "Freshdesk Glue Job"
    bes_crm_salesforce_name         = "Salesforce Glue Job"
  }
}

inputs = {
  platform_gc_forms_job_name      = dependency.glue.outputs.platform_gc_forms_job_name
  platform_gc_notify_job_name     = dependency.glue.outputs.platform_gc_notify_job_name
  platform_support_freshdesk_name = dependency.glue.outputs.platform_support_freshdesk_name
  bes_crm_salesforce_name         = dependency.glue.outputs.bes_crm_salesforce_name
  curated_bucket_name             = dependency.buckets.outputs.curated_bucket_name
  athena_bucket_name              = dependency.buckets.outputs.athena_bucket_name
  transformed_bucket_name         = dependency.buckets.outputs.transformed_bucket_name
}

include {
  path = find_in_parent_folders("root.hcl")
}
