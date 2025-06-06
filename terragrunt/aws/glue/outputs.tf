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


output "platform_gc_forms_job_name" {
  description = "Gc Forms Glue job name."
  value       = aws_glue_job.platform_gc_forms_job.name
}

output "platform_gc_notify_job_name" {
  description = "Gc Notify Glue job name."
  value       = aws_glue_job.platform_gc_notify_job.name
}
output "platform_support_freshdesk_name" {
  description = "Freshdesk Glue job name."
  value       = aws_glue_job.platform_support_freshdesk.name
}

output "bes_crm_salesforce_name" {
  description = "Salesforce Glue job name."
  value       = aws_glue_job.bes_crm_salesforce.name
}
