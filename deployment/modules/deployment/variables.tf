variable "aws_resource_prefix" {
  default = "ccproxy-"
}

variable "layer_zip_path" {
  type = string
}

variable "package_zip_path" {
  type = string
}

variable "lambda_runtime" {
  type = string
  default = "python3.10"
}