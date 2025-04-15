locals {
  # Remove all objects after expiry
  lifecycle_expire_all = {
    id      = "expire_all"
    enabled = true
    expiration = {
      days = "30"
    }
  }
  # GC Notify expire old export data
  lifecycle_expire_gc_notify = {
    id      = "expire_gc_notify"
    enabled = true
    prefix  = "platform/gc-notify/"
    expiration = {
      days = "3"
    }
  }
  # Cleanup old versions and incomplete uploads
  lifecycle_remove_noncurrent_versions = {
    id                                     = "remove_noncurrent_versions"
    enabled                                = true
    abort_incomplete_multipart_upload_days = "7"
    noncurrent_version_expiration = {
      days = "30"
    }
  }
  # Transition objects to cheaper storage classes over time
  lifecycle_transition_storage = {
    id      = "transition_storage"
    enabled = true
    transition = [
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