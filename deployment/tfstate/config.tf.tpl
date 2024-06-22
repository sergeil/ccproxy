terraform {
  required_version = ">= 1.4.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.6.0"
    }
  }
}

provider "aws" {
  region  = "$region"
  profile = "$profile"
}