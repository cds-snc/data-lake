variable "account_id" {
  description = "The AWS account ID"
  type        = string
}

variable "billing_tag_value" {
  description = "The billing tag value to apply to resources."
  type        = string
}

variable "env" {
  description = "The environment for the resources."
  type        = string
}

variable "region" {
  description = "The AWS region"
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

variable "raw_bucket_arn" {
  description = "The ARN of the Raw bucket"
  type        = string
}

variable "raw_bucket_name" {
  description = "The name of the Raw bucket"
  type        = string
}