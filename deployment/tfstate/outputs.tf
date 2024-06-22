output "bucket" {
  value = aws_s3_bucket.state_bucket.bucket
}

output "table" {
  value = aws_dynamodb_table.state_lock_db.name
}
