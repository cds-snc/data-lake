variable "curated_bucket_arn" {
  description = "The ARN of the Curated bucket"
  type        = string
}

variable "curated_bucket_name" {
  description = "The name of the Curated bucket"
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

variable "gx_bucket_arn" {
  description = "The ARN of the Grreat Expectations bucket"
  type        = string
}

variable "gx_bucket_name" {
  description = "The name of the Grreat Expectations bucket"
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
