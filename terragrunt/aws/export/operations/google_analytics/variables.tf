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

variable "raw_bucket_arn" {
  description = "The ARN of the Raw bucket"
  type        = string
}

variable "raw_bucket_name" {
  description = "The name of the Raw bucket"
  type        = string
}

variable "gcp_project_number" {
  description = "Google Cloud Platform project number"
  type        = string
}

variable "gcp_pool_id" {
  description = "Google Cloud Workload Identity Pool ID"
  type        = string
}

variable "gcp_provider_id" {
  description = "Google Cloud Workload Identity Provider ID"
  type        = string
}

variable "gcp_service_account_email" {
  description = "Google Cloud Service Account email for authentication"
  type        = string
}

variable "gcp_ga_property_forms_marketing_site" {
  description = "Google Analytics Property ID for Forms Marketing Site"
  type        = string
}

variable "gcp_ga_property_notification_ga4" {
  description = "Google Analytics Property ID for Notification GA4"
  type        = string
}

variable "gcp_ga_property_platform_form_client" {
  description = "Google Analytics Property ID for Platform Form Client"
  type        = string
}

variable "gcp_ga_property_platform_core_superset_doc" {
  description = "Google Analytics Property ID for Platform Core Superset Doc"
  type        = string
}