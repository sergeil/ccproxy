#!/bin/bash

set -eu

if [ ! -x "$(command -v terraform)" ]; then
    echo "Terraform is required to run this script, aborting ..."
    exit 1
fi

script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${script_path}/..
deployment_dir=$(pwd)

echo "# Use credentials that you use to login to ComfortClick app:"
read -p "Config file: " config_file_path
read -sp "Password: " password
echo

login_url=$(terraform output -raw login_url)

project_root_dir=${deployment_dir}/..
cd $project_root_dir

export PYTHONPATH="$PYTHONPATH:$(pwd)"
set +e
result=$(python ccproxy/cli.py create-account ${login_url} ${config_file_path} ${password})

if [ "$?" == 0 ]; then
    echo "# Goodstuff, a new account has been created on ccproxy: ${result}"
else
    echo "# Something went wrong: ${result}"
    exit 1
fi