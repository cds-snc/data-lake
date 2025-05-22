output "athena_bucket_arn" {
  description = "ARN of the S3 Athena query result bucket."
  value       = module.athena_bucket.s3_bucket_arn
}

output "athena_bucket_name" {
  description = "Name of the S3 Athena query result bucket."
  value       = module.athena_bucket.s3_bucket_id
}

output "curated_bucket_arn" {
  description = "ARN of the S3 Curated data bucket."
  value       = module.curated_bucket.s3_bucket_arn
}

output "curated_bucket_name" {
  description = "Name of the S3 Curated data bucket."
  value       = module.curated_bucket.s3_bucket_id
}

output "glue_bucket_arn" {
  description = "ARN of the S3 Glue data bucket."
  value       = module.glue_bucket.s3_bucket_arn
}

output "glue_bucket_name" {
  description = "Name of the S3 Glue data bucket."
  value       = module.glue_bucket.s3_bucket_id
}

output "gx_bucket_arn" {
  description = "ARN of the S3 GX data bucket."
  value       = module.gx_bucket.s3_bucket_arn
}

output "gx_bucket_name" {
  description = "Name of the S3 GX data bucket."
  value       = module.gx_bucket.s3_bucket_id
}

output "raw_bucket_arn" {
  description = "ARN of the S3 Raw data bucket."
  value       = module.raw_bucket.s3_bucket_arn
}

output "raw_bucket_name" {
  description = "Name of the S3 Raw data bucket."
  value       = module.raw_bucket.s3_bucket_id
}

output "transformed_bucket_arn" {
  description = "ARN of the S3 Transformed data bucket."
  value       = module.transformed_bucket.s3_bucket_arn
}

output "transformed_bucket_name" {
  description = "Name of the S3 Transformed data bucket."
  value       = module.transformed_bucket.s3_bucket_id
}
