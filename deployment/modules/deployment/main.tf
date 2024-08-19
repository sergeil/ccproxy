locals {
  host_and_username_gsi = "HostAndUsernameIndex"
}

###

resource "aws_dynamodb_table" "auth" {
  name         = "${var.aws_resource_prefix}auth"
  hash_key     = "id"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "host"
    type = "S"
  }

  global_secondary_index {
    name            = local.host_and_username_gsi
    hash_key        = "host"
    projection_type = "ALL"
  }
}

###

resource "aws_iam_policy" "lambda" {
  name_prefix = "${var.aws_resource_prefix}lambda-"
  policy = templatefile("${path.module}/templates/lambda_policy.tpl", {
    table_arn             = aws_dynamodb_table.auth.arn
    host_and_username_gsi = local.host_and_username_gsi
  })
}

resource "aws_iam_role" "lambda" {
  name_prefix        = "${var.aws_resource_prefix}lambda-"
  assume_role_policy = file("${path.module}/templates/lambda_role.json")
}

resource "aws_iam_role_policy_attachment" "action_processor" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda.arn
}

resource "aws_lambda_layer_version" "this" {
  filename         = var.layer_zip_path
  source_code_hash = filebase64sha256(var.layer_zip_path)
  layer_name       = "${var.aws_resource_prefix}py"

  compatible_runtimes = [var.lambda_runtime]
}

resource "aws_lambda_function" "process_action" {
  function_name = "${var.aws_resource_prefix}main"
  handler       = "ccproxy.handlers.process_action.process_action_handler"
  role          = aws_iam_role.lambda.arn
  runtime       = var.lambda_runtime
  memory_size   = 256
  timeout       = 10

  filename         = var.package_zip_path
  source_code_hash = filebase64sha256(var.package_zip_path)
  description      = "Entry point for iOS shortcuts automation for ComfortClick"

  layers = [aws_lambda_layer_version.this.arn]

  environment {
    variables = {
      ACCOUNTS_TABLE = aws_dynamodb_table.auth.name
    }
  }
}

###

resource "aws_lambda_function_url" "process_action" {
  function_name      = aws_lambda_function.process_action.function_name
  authorization_type = "NONE"
}

resource "aws_lambda_function" "login" {
  function_name = "${var.aws_resource_prefix}login"
  handler       = "ccproxy.handlers.login.login_handler"
  role          = aws_iam_role.lambda.arn
  runtime       = var.lambda_runtime
  memory_size   = 256
  timeout       = 10

  filename         = var.package_zip_path
  source_code_hash = filebase64sha256(var.package_zip_path)
  description      = "Authentication endpoint for ComfortClick"

  layers = [aws_lambda_layer_version.this.arn]

  environment {
    variables = {
      ACCOUNTS_TABLE = aws_dynamodb_table.auth.name
    }
  }
}

resource "aws_lambda_function_url" "login" {
  function_name      = aws_lambda_function.login.function_name
  authorization_type = "NONE"
}

### 

resource "aws_lambda_function" "update_account" {
  function_name = "${var.aws_resource_prefix}update_account"
  handler       = "ccproxy.handlers.update_account.update_account"
  role          = aws_iam_role.lambda.arn
  runtime       = var.lambda_runtime
  memory_size   = 256
  timeout       = 10

  filename         = var.package_zip_path
  source_code_hash = filebase64sha256(var.package_zip_path)
  description      = "Account update endpoint"

  layers = [aws_lambda_layer_version.this.arn]

  environment {
    variables = {
      ACCOUNTS_TABLE = aws_dynamodb_table.auth.name
    }
  }
}

resource "aws_lambda_function_url" "update_account" {
  function_name      = aws_lambda_function.update_account.function_name
  authorization_type = "NONE"
}

