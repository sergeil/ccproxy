module "deployment" {
  source = "./modules/deployment"

  layer_zip_path   = "${path.module}/artifacts/layer.zip"   # use "bin/build-layers.sh"
  package_zip_path = "${path.module}/artifacts/package.zip" # use "bin/build-package.sh"
}

module "lambda_tender" {
  source = "./modules/lambda-tender"

  lambda_arn = module.deployment.process_action_lambda_arn
}

output "login_url" {
  value = module.deployment.login_url
}

output "process_action_url" {
  value = module.deployment.process_action_url
}

output "update_account_url" {
  value = module.deployment.update_account_url
}