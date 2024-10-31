locals {
  # Remove all objects after expiry
  lifecycle_expire_all = {
    id      = "expire_all"
    enabled = true
    expiration = {
      days                         = "30"
      expired_object_delete_marker = true
    }
  }
  # Cleanup old versions and incomplete uploads
  lifecycle_remove_noncurrent_versions = {
    id      = "remove_noncurrent_versions"
    enabled = true
    noncurrent_version_expiration = {
      days = "30"
    }
    abort_incomplete_multipart_upload = {
      days_after_initiation = "1"
    }
  }
  # Transition objects to cheaper storage classes over time
  lifecycle_transition_storage = {
    id      = "transition_storage"
    enabled = true
    transitions = [
      {
        days          = "90"
        storage_class = "STANDARD_IA"
      },
      {
        days          = "180"
        storage_class = "GLACIER"
      }
    ]
  }
}