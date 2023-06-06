#!/usr/bin/env bash

aws cloudformation create-stack \
  --stack-name test-smh-api-deploy \
  --template-body file://smh-api-test-deploy.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM \
  --tags '[{"Key":"Environment","Value":"test"},{"Key":"Cost_Centre","Value":"Central"},{"Key":"Expiry","Value":"Never"},{"Key":"Project","Value":"SMH API Test Deployment"},{"Key":"Purpose","Value":"Deploy SMH API to TEST environment"},{"Key":"Name","Value":"test-smh-api-deploy"},{"Key":"workload-monitoring","Value":"test"}]'

