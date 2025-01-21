locals {
  # To grant a Superset IAM role access to a Glue catalog database, the role ARN must end with the database name:
  # - arn:aws:iam::123456789012:role/SupersetAthenaRead-datatabase_name
  # The Superset role ARNs are managed by the `superset_iam_role_arns` input variable.
  glue_catalog_databases = [
    "all", # special case for an IAM role with access to all databases
    aws_glue_catalog_database.operations_aws_production.name,
    aws_glue_catalog_database.platform_gc_forms_production.name,
    aws_glue_catalog_database.platform_support_production.name,
  ]
  glue_crawler_log_group_name = "/aws-glue/crawlers-role${aws_iam_role.glue_crawler.path}${aws_iam_role.glue_crawler.name}-${aws_glue_security_configuration.encryption_at_rest.name}"
  glue_etl_log_group_name     = "/aws-glue/jobs/${aws_glue_security_configuration.encryption_at_rest.name}-role${aws_iam_role.glue_crawler.path}${aws_iam_role.glue_etl.name}"
}