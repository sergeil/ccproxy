{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "${lambda_arn}:*",
                "${lambda_arn}"
            ]
        }
    ]
}