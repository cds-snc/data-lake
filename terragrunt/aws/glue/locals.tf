locals {
  is_production = var.env == "production"

  # To grant a Superset IAM role access to a Glue catalog database, the role ARN must end with the database name:
  # - arn:aws:iam::123456789012:role/SupersetAthenaRead-datatabase_name
  # The Superset role ARNs are managed by the `superset_iam_role_arns` input variable.
  glue_catalog_databases = [
    aws_glue_catalog_database.operations_aws_production.name,
    aws_glue_catalog_database.operations_github_production.name,
    aws_glue_catalog_database.operations_google_analytics_production.name,
    aws_glue_catalog_database.platform_gc_forms_production.name,
    aws_glue_catalog_database.platform_gc_notify_production.name,
    aws_glue_catalog_database.platform_support_production.name,
    aws_glue_catalog_database.bes_crm_salesforce_production.name,
    aws_glue_catalog_database.platform_gc_design_system.name,
  ]

  # Filter out any Glue databases without a corresponding Superset IAM role
  glue_catalog_databases_superset_access = toset([
    for database_name in local.glue_catalog_databases : database_name
    if length([
      for arn in var.superset_iam_role_arns : arn
      if endswith(arn, database_name)
    ]) > 0
  ])

  glue_crawler_log_group_name         = "/aws-glue/crawlers-role${aws_iam_role.glue_crawler.path}${aws_iam_role.glue_crawler.name}-${aws_glue_security_configuration.encryption_at_rest.name}"
  glue_etl_pythonshell_log_group_name = "/aws-glue/python-jobs/${aws_glue_security_configuration.encryption_at_rest.name}-role${aws_iam_role.glue_crawler.path}${aws_iam_role.glue_etl.name}"
  glue_etl_spark_log_group_name       = "/aws-glue/jobs/${aws_glue_security_configuration.encryption_at_rest.name}-role${aws_iam_role.glue_crawler.path}${aws_iam_role.glue_etl.name}"

  s3_bes_prefix                = "bes"
  s3_bes_strategic_data_prefix = "${local.s3_bes_prefix}/strategic-data"
}