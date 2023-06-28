#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: sh upload_to_s3.sh <stage> <backet_path> <aws profile>" 1>&2
  exit 1
fi

stage=$1
backet_path=$2
aws_profile=$3

aws s3 sync ./dist/ s3://$backet_path --profile $aws_profile
