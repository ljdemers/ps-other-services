#!/usr/bin/env bash

aws cloudformation update-stack \
  --stack-name smh-api-test-runner \
  --template-body file://smh-api-test-runner.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM
