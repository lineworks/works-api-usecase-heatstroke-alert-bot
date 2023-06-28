#!/bin/sh

if [ $# -ne 4 ]; then
  echo "Usage: sh deploy_backend_aws.sh <bot id> <author> <stage> <aws profile>" 1>&2
  exit 1
fi

bot_id=$1
author=$2
stage=$3
aws_profile=$4

echo "Bot ID: $bot_id"
echo "Author: $author"
echo "Stage: $stage"
echo "AWS Profile: $aws_profile"
echo

pushd ./backend
sls deploy --param="bot_id=$bot_id" --param="author=$author" --param="dep=PandG" --stage $stage --aws-profile $aws_profile --verbose
popd

echo "Done"
