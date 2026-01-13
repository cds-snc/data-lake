variable "athena_bucket_arn" {
  description = "The ARN of the Athena bucket"
  type        = string
}

variable "athena_bucket_name" {
  description = "The name of the Athena bucket"
  type        = string
}

variable "glue_bucket_arn" {
  description = "The ARN of the Glue bucket"
  type        = string
}

variable "glue_bucket_name" {
  description = "The name of the Glue bucket"
  type        = string
}

variable "raw_bucket_arn" {
  description = "The ARN of the Raw bucket"
  type        = string
}

variable "raw_bucket_name" {
  description = "The name of the Raw bucket"
  type        = string
}

variable "transformed_bucket_arn" {
  description = "The ARN of the Transformed bucket"
  type        = string
}

variable "transformed_bucket_name" {
  description = "The name of the Transformed bucket"
  type        = string
}

variable "qualtrics_external_id" {
  description = "External ID for Qualtrics cross-account access"
  type        = string
  sensitive   = true
}
