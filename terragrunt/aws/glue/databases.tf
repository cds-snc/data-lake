resource "aws_glue_catalog_database" "operations_aws_production" {
  name        = "operations_aws_production"
  description = "TRANSFORMED: data source path: /operations/aws/*"
}

resource "aws_glue_catalog_database" "operations_aws_production_raw" {
  name        = "operations_aws_production_raw"
  description = "RAW: data source path: /operations/aws/*"
}