terraform {
  required_version = ">= 1.4.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.9"
    }
  }

  backend "s3" {
    region         = "$region"
    profile        = "$profile"
    bucket         = "$state_bucket_name"
    dynamodb_table = "$state_bucket_table"
    key            = "terraform.tfstate"
  }
}

provider "aws" {
  region  = "$region"
  profile = "$profile"
}
