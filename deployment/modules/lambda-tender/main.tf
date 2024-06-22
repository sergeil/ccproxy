resource "aws_scheduler_schedule" "this" {
  name_prefix = "${var.aws_resource_prefix}schedule-"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = var.schedule

  target {
    arn      = var.lambda_arn
    role_arn = aws_iam_role.this.arn

    input = jsonencode({
      "lambda_tender" : true
    })
  }
}

resource "aws_iam_role" "this" {
  name_prefix = "${var.aws_resource_prefix}role-"

  inline_policy {
    name = "${var.aws_resource_prefix}policy-"

    policy = templatefile("${path.module}/templates/policy.json.tpl", {
      lambda_arn = var.lambda_arn
    })
  }

  assume_role_policy = file("${path.module}/templates/role.json")
}

variable "aws_resource_prefix" {
  type    = string
  default = "lambda_tender-"
}

variable "lambda_arn" {
  type = string
}

variable "schedule" {
  type    = string
  default = "rate(4 minutes)"
}
