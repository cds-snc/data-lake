output "athena_workgroup_name" {
  description = "The name of the Athena workgroup."
  value       = aws_athena_workgroup.data_lake.name
}

output "athena_curated_workgroup_name" {
  description = "The name of the Athena workgroup for curated data."
  value       = aws_athena_workgroup.data_lake_curated.name
}