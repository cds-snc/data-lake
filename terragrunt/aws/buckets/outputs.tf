output "curated_bucket_arn" {
  description = "ARN of the S3 Curated data bucket."
  value       = module.curated_bucket.s3_bucket_arn
}

output "curated_bucket_name" {
  description = "Name of the S3 Curated data bucket."
  value       = module.curated_bucket.s3_bucket_id
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
