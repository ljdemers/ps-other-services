#!/usr/bin/env bash

aws cloudformation create-stack \
  --stack-name smh-api-test-runner \
  --template-body file://smh-api-test-runner.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM \
  --tags '[{"Key":"Environment","Value":"test"},{"Key":"Cost_Centre","Value":"Central"},{"Key":"Expiry","Value":"Never"},{"Key":"Project","Value":"urpletrac SMH API Test Runner"},{"Key":"Purpose","Value":"SMH API test runners"},{"Key":"Name","Value":"smh-api-test-runner"},{"Key":"workload-monitoring","Value":"test"}]'

