#!/usr/bin/env bash

aws cloudformation update-stack \
  --stack-name test-screening-workers-deploy \
  --template-body file://screening-workers-test-deploy.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM
