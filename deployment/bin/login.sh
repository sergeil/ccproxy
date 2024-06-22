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
read -p "Host: " host
read -p "Username: " username
read -sp "Password: " password
echo

body="{ \"host\": \"${host}\", \"username\": \"${username}\", \"password\": \"${password}\" }"
login_url=$(terraform output -raw login_url)

response=$(curl -i -o - -s -X POST ${login_url} -H "Content-Type: application/json" -d "${body}")
http_status=$(echo "${response}" | grep HTTP |  awk '{print $2}')
response_body=$(echo "${response}" | tail -n1)

if [[ "${http_status}" == 200 ]]; then
    process_action_url=$(terraform output -raw process_action_url)
    echo ""
    echo "# Goodstuff, account '${response_body}' has been created on ccproxy!"
    echo "# After you have updated and deployed config.json file, you can start issuing requests"
    echo "# to your CC backend via ccproxy, e.g.: "
    echo "# ${process_action_url}?action=open_garage_door"
else
    echo "# Authentication error: "
    echo $response_body
    exit 1
fi