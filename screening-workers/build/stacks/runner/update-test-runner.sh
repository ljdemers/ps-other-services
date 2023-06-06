#!/usr/bin/env bash

aws cloudformation update-stack \
  --stack-name screening-workers-test-runner \
  --template-body file://screening-workers-test-runner.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM
