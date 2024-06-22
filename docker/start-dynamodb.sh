#!/bin/bash

set -e

script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${script_path}

rm -rf volumes/dynamodb/shared-local-instance.db

if [[ $- == *i* ]]
then
  echo "Starting DynamoDB in a foreground\n"
  docker-compose -f local-dynamodb.yml up
else 
  echo -e "Starting DynamoDB as a background job\n"
  docker-compose -f local-dynamodb.yml up -d
fi
