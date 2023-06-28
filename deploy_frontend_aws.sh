#!/bin/sh

if [ $# -ne 3 ]; then
  echo "Usage: sh deploy_frontend_aws.sh <stage> <backet_path> <aws profile>" 1>&2
  exit 1
fi

stage=$1
backet_path=$2
aws_profile=$3

pushd ./frontend
echo "build"
npm run build-$stage
echo "upload to s3"
sh upload_to_s3.sh $stage $backet_path $aws_profile
popd
