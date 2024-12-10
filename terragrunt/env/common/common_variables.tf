variable "account_id" {
  description = "(Required) The account ID to perform actions on."
  type        = string
}

variable "billing_tag_value" {
  description = "(Required) the value we use to track billing"
  type        = string
}

variable "env" {
  description = "(Required) The current running environment"
  type        = string
}

variable "region" {
  description = "(Required) The region to build infra in"
  type        = string
}

variable "superset_iam_role_arns" {
  description = "(Required) The ARNs of the IAM role that Superset uses to access the Glue catalog"
  type        = list(string)
}