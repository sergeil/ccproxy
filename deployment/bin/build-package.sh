#!/bin/bash

set -eu

script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${script_path}/../../
project_root_dir=$(pwd)

function verify_file_exists() {
  filename=$1

  if [[ ! -f $filename ]]; then
    echo "File '${filename}' doesn't exist. Please refer to README.md for more info on how to create it."
    exit 1
  fi
}

cd $project_root_dir

tmp_dir=$(mktemp -d -t ccproxy-lambda-package-)
trap "rm -rf ${tmp_dir}" EXIT
cp -r ${project_root_dir}/ccproxy ${tmp_dir}/
verify_file_exists ${project_root_dir}/.env.prod
cp ${project_root_dir}/.env.prod ${tmp_dir}/.env
verify_file_exists ${project_root_dir}/config.json
cp ${project_root_dir}/config.json ${tmp_dir}/

zip_filepath=${project_root_dir}/deployment/artifacts/package.zip
cd $tmp_dir
zip -rq $zip_filepath .

echo $zip_filepath