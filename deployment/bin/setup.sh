#!/bin/bash

set -eu

script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${script_path}/..
deployment_dir=$(pwd)
project_dir=${deployment_dir}/..

if [ ! -x "$(command -v terraform)" ]; then
    echo "Terraform is required to run this script, aborting ..."
    exit 1
fi

compile_config_tf() {
    local file_path=$1

    sed -i '' "s/\$region/${aws_region}/g" ${file_path}
    if [ "${aws_profile}" == 'default' ]; then
        sed -i '' '/\$profile/d' ${file_path}
    else
        sed -i '' "s/\$profile/${aws_profile}/g" ${file_path}
    fi
}

main_tf_config_filename=config.tf
main_tf_config_tpl_filename=config.tf.tpl
main_tf_config_filepath=${deployment_dir}/${main_tf_config_filename}

tfstate_filename=config.tf
tfstate_tpl_filename=config.tf.tpl
tfstate_dir=${deployment_dir}/tfstate
tfstate_filepath=${tfstate_dir}/${tfstate_filename}

# --- --- ---

echo "# Enter a name of a region where infrastructure will be deployed,"
echo "# leave empty for detault: eu-west-1"
echo "# All available regions can be found, for example, here: "
echo "# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html"
read -p "Region: " aws_region
echo ""
if [ -z "${aws_region}" ]; then
    aws_region='eu-west-1'
fi

echo "# Name of ~/.aws/credentials profile to use, leave empty for a default one (i.e. \"ccproxy\")"
echo "# (unless you want to tweak deployment process, leave empty)"
echo "# "
echo "# More infomation: "
echo "# https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html"
read -p "Profile: " aws_profile
echo ""
if [ -z "${aws_profile}" ]; then
    aws_profile='ccproxy'
fi

# --- --- ---

echo "# Initializing and provisioning Terraform state backend"
cd $tfstate_dir
cp ${tfstate_tpl_filename} ${tfstate_filename}
compile_config_tf ${tfstate_filename}
echo "${tfstate_filename} successfully created"

terraform init
terraform apply -auto-approve
cd $deployment_dir

cd $tfstate_dir
tfstate_bucket=$(terraform output -raw bucket)
tfstate_table=$(terraform output -raw table)

# --- --- ---

echo -e "\n# Building binaries and provisioning infrastructure"
cd $deployment_dir
cp ${main_tf_config_tpl_filename} ${main_tf_config_filename}
compile_config_tf ${main_tf_config_filename}
sed -i '' "s/\$state_bucket_name/${tfstate_bucket}/g" ${main_tf_config_filename}
sed -i '' "s/\$state_bucket_table/${tfstate_table}/g" ${main_tf_config_filename}
echo "${main_tf_config_filepath} successfully created"
terraform init

mkdir -p ${deployment_dir}/artifacts/
cd $project_dir
make build-layer
make build-package
echo -e "\n# Binaries were successfully built, deploying ..."
make infra OPTS="-auto-approve"
echo -e "\n\n\n"

cd $deployment_dir
login_url=$(terraform output -raw login_url)
process_action_url=$(terraform output -raw process_action_url)
echo "# Good stuff, the infra has been provisioned. Here are your URLs: "
echo "# * login_url: ${login_url}"
echo "# * process_action_url: ${process_action_url}"
echo "# Now you can run 'make create-account' to create an account on ccproxy."