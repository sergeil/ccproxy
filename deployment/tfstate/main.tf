resource "aws_s3_bucket" "state_bucket" {
  bucket_prefix = "${var.resource_name_prefix}tf-state-"

  force_destroy = true

  tags = {
    Name = "Terraform state storage."
  }
}

resource "aws_s3_bucket_versioning" "state_bucket_versioning" {
  bucket = aws_s3_bucket.state_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_dynamodb_table" "state_lock_db" {
  name         = "${var.resource_name_prefix}tf-state-lock"
  hash_key     = "LockID"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "Terraform state locking."
  }
}
