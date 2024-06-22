#!/bin/bash

set -eu

if [ ! -x "$(command -v docker)" ]; then
    echo "Docker is required to run this script, aborting ..."
    exit 1
fi

script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${script_path}/../../
project_root_dir=$(pwd)

tmp_root_dir=$(mktemp -d -t ccproxy-)
rm -rf $tmp_root_dir
trap "rm -rf ${tmp_root_dir}" EXIT
cp -r $project_root_dir $tmp_root_dir
cd $tmp_root_dir

# TODO think - maybe we can just specify target platform and no need to run it inside
# a docker container, mm?
docker run \
  --rm -it \
  -v $(pwd):/mnt/tmp \
  -w /mnt/tmp oz123/pipenv:3.10-2023.07.23 bash \
  -c "cd deployment/bin && ./_install-linux-deps.sh"

venv_dir=$tmp_root_dir/.venv
cd $venv_dir/lib
python_dir=$(ls)
cd $python_dir/site-packages
deps_dir=$(pwd)

cd $tmp_root_dir

tmp_layer_dir=$(mktemp -d -t ccproxy-lambda-layer-)
trap "rm -rf ${tmp_layer_dir}" EXIT
mkdir ${tmp_layer_dir}/python
cp -r $deps_dir/* ${tmp_layer_dir}/python/

zip_filepath=${project_root_dir}/deployment/artifacts/layer.zip
cd $tmp_layer_dir
zip -rq $zip_filepath .
echo -e "\n$zip_filepath"