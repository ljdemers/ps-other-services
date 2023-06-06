#!/usr/bin/env bash

aws cloudformation create-stack \
  --stack-name screening-api-test-runner \
  --template-body file://screening-api-test-runner.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM \
  --tags '[{"Key":"Environment","Value":"test"},{"Key":"Cost_Centre","Value":"Central"},{"Key":"Expiry","Value":"Never"},{"Key":"Project","Value":"Screening API Test Runner"},{"Key":"Purpose","Value":"Screening API test runners"},{"Key":"Name","Value":"screening-api-test-runner"},{"Key":"workload-monitoring","Value":"test"}]'
