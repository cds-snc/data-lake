resource "aws_glue_catalog_database" "operations_aws_production" {
  name        = "operations_aws_production"
  description = "Data source path: /operations/aws/*"
}