#!/usr/bin/env bash

aws cloudformation update-stack \
  --stack-name test-screening-api-deploy \
  --template-body file://screening-api-test-deploy.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM
