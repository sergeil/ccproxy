#!/bin/bash

set -eu

script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $script_path/../

terraform destroy
rm -rf .terraform config.tf

cd tfstate
terraform destroy
rm -rf .terraform config.tf terraform.tfstate terraform.tfstate.backup

echo "# Great success, all ccproxy related infra has been destroyed."