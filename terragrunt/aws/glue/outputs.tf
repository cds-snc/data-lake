output "glue_crawler_log_group_name" {
  description = "The name of the Glue Crawler CloudWatch log group."
  value       = local.glue_crawler_log_group_name
}

output "glue_etl_pythonshell_log_group_name" {
  description = "The name of the Glue ETL CloudWatch log group used by `pythonshell` Glue jobs."
  value       = local.glue_etl_pythonshell_log_group_name
}

output "glue_etl_spark_log_group_name" {
  description = "The name of the Glue ETL CloudWatch log group used by `spark` Glue jobs."
  value       = local.glue_etl_spark_log_group_name
}