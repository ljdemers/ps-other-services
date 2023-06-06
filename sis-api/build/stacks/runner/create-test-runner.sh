#!/usr/bin/env bash

aws cloudformation create-stack \
  --stack-name sis-test-runner \
  --template-body file://sis-test-runner.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM \
  --tags '[{"Key":"Environment","Value":"test"},{"Key":"Cost_Centre","Value":"Central"},{"Key":"Expiry","Value":"Never"},{"Key":"Project","Value":"SIS Test Runner"},{"Key":"Purpose","Value":"SIS test runners"},{"Key":"Name","Value":"sis-test-runner"},{"Key":"workload-monitoring","Value":"test"}]'

