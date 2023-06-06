#!/usr/bin/env bash

aws cloudformation create-stack \
  --stack-name screening-workers-test-runner \
  --template-body file://screening-workers-test-runner.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM \
  --tags '[{"Key":"Environment","Value":"test"},{"Key":"Cost_Centre","Value":"Central"},{"Key":"Expiry","Value":"Never"},{"Key":"Project","Value":"Screening Workers Test Runner"},{"Key":"Purpose","Value":"Screening Workers test runners"},{"Key":"Name","Value":"screening-workers-test-runner"},{"Key":"workload-monitoring","Value":"test"}]'
