resource "aws_glue_catalog_database" "platform_gc_forms_production" {
  name        = "platform_gc_forms_production"
  description = "TRANSFORMED: data source path: /platform/gc-forms/*"
}

resource "aws_glue_catalog_database" "platform_gc_forms_production_raw" {
  name        = "platform_gc_forms_production_raw"
  description = "RAW: data source path: /platform/gc-forms/*"
}

resource "aws_glue_catalog_database" "platform_gc_notify_production" {
  name        = "platform_gc_notify_production"
  description = "TRANSFORMED: data source path: /platform/gc-notify/*"
}

resource "aws_glue_catalog_database" "platform_support_production" {
  name        = "platform_support_production"
  description = "TRANSFORMED: data source path: /platform/support/*"
}

resource "aws_glue_catalog_database" "platform_support_production_raw" {
  name        = "platform_support_production_raw"
  description = "RAW: data source path: /platform/support/*"
}

resource "aws_glue_catalog_database" "bes_crm_salesforce_production" {
  name        = "bes_crm_salesforce_production"
  description = "TRANSFORMED: data source path: /bes/crm/salesforce/*"
}

resource "aws_glue_catalog_database" "operations_aws_production" {
  name        = "operations_aws_production"
  description = "TRANSFORMED: data source path: /operations/aws/*"
}

resource "aws_glue_catalog_database" "operations_aws_production_raw" {
  name        = "operations_aws_production_raw"
  description = "RAW: data source path: /operations/aws/*"
}