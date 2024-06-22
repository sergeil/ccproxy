output "login_url" {
  value = aws_lambda_function_url.login.function_url
}

output "process_action_url" {
  value = aws_lambda_function_url.process_action.function_url
}

output "process_action_lambda_arn" {
  value = aws_lambda_function.process_action.arn
}
