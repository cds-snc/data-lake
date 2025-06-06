variable "athena_bucket_name" {
  description = "The name of the Athena bucket"
  type        = string
}

variable "curated_bucket_name" {
  description = "The name of the curated S3 bucket for Athena query outputs"
  type        = string
}
