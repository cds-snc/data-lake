resource "aws_glue_catalog_database" "platform_gc_forms_production" {
  name        = "platform_gc_forms_production"
  description = "TRANSFORMED: data source path: /platform/gc-forms/*"
}

resource "aws_glue_catalog_database" "platform_support_production_raw" {
  name        = "platform_support_production_raw"
  description = "RAW: data source path: /platform/support/*"
}

resource "aws_glue_catalog_database" "operations_aws_production" {
  name        = "operations_aws_production"
  description = "TRANSFORMED: data source path: /operations/aws/*"
}

resource "aws_glue_catalog_database" "operations_aws_production_raw" {
  name        = "operations_aws_production_raw"
  description = "RAW: data source path: /operations/aws/*"
}