#!/usr/bin/env bash

aws cloudformation update-stack \
  --stack-name sis-test-runner \
  --template-body file://sis-test-runner.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM
