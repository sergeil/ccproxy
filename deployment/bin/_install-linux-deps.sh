#!/bin/bash

# Meant to be run only in Docker container, and by build-layer.sh only

set -eu

script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${script_path}/../../
project_root_dir=$(pwd)

echo "# Installing Lambda env compatible dependencies"
PIPENV_VENV_IN_PROJECT=1 pipenv sync 

venv_dir=$(pipenv --venv)
cd ${venv_dir}/lib
python_dir=$(ls)
cd ${python_dir}/site-packages
site_packages_dir=$(pwd)

echo -e "\n# Installing Lambda env compatible cryptography"
# https://github.com/pyca/cryptography/issues/6390
# https://github.com/pyca/cryptography/issues/6391#issuecomment-976172880
pipenv run pip install \
  --platform manylinux2014_x86_64 \
  --target=$site_packages_dir \
  --implementation cp \
  --only-binary=:all: \
  --upgrade cryptography