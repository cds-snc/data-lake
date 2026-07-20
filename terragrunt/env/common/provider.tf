
terraform {
  required_version = "1.15.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.account_id]

  default_tags {
    tags = {
      CostCentre = "PlatformDataLake"
      Terraform  = true
      ssc_cbrid  = "22DI"
    }
  }
}
