variable "platform_gc_forms_job_name" {
  description = "GC Forms Glue job name."
  type        = string
}

variable "platform_gc_notify_job_name" {
  description = "GC Notify Glue job name."
  type        = string
}

variable "platform_support_freshdesk_name" {
  description = "Freshdesk Glue job name."
  type        = string
}

variable "bes_crm_salesforce_name" {
  description = "Salesforce Glue job name."
  type        = string
}

variable "curated_bucket_name" {
  description = "Curated bucket name where the Glue jobs will write their output."
  type        = string
}

variable "athena_curated_workgroup_name" {
  description = "The name of the Athena workgroup for curated tables."
  type       = string
}

variable "athena_bucket_name" {
  description = "The name of the Athena bucket."
  type       = string
}

variable "transformed_bucket_name" {
  description = "The name of the Athena bucket."
  type       = string
}
