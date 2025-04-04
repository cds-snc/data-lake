output "glue_crawler_log_group_name" {
  description = "The name of the Glue Crawler CloudWatch log group."
  value       = local.glue_crawler_log_group_name
}

output "glue_etl_log_group_name" {
  description = "The name of the Glue ETL CloudWatch log group."
  value       = local.glue_etl_log_group_name
}