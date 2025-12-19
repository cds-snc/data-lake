inputs = {
  account_id        = "739275439843"
  env               = "production"
  billing_tag_value = "PlatformDataLake"

  superset_iam_role_arns = [
    "arn:aws:iam::066023111852:role/SupersetAthenaRead-operations_aws_production",
    "arn:aws:iam::066023111852:role/SupersetAthenaRead-operations_github_production",
    "arn:aws:iam::066023111852:role/SupersetAthenaRead-operations_google_analytics_production",
    "arn:aws:iam::066023111852:role/SupersetAthenaRead-platform_gc_forms_production",
    "arn:aws:iam::066023111852:role/SupersetAthenaRead-platform_gc_notify_production",
    "arn:aws:iam::066023111852:role/SupersetAthenaRead-platform_gc_design_system_production",
    "arn:aws:iam::066023111852:role/SupersetAthenaRead-platform_support_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-operations_aws_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-operations_github_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-operations_google_analytics_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-platform_gc_forms_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-platform_gc_notify_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-platform_gc_design_system_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-platform_support_production",
    "arn:aws:iam::257394494478:role/SupersetAthenaRead-bes_crm_salesforce_production"
  ]
}