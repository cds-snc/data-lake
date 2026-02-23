inputs = {
  account_id        = "454671348950"
  env               = "staging"
  billing_tag_value = "PlatformDataLake"

  superset_iam_role_arns = [
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-platform_gc_forms_staging",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-platform_gc_notify_staging",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-platform_support_staging",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-platform_gc_design_system_staging",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-operations_github_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-operations_google_analytics_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-operations_qualtrics_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-unified_staging",

  ]
}