#!/usr/bin/env bash

aws cloudformation update-stack \
  --stack-name test-sis-api-deploy \
  --template-body file://sis-api-test-deploy.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM
