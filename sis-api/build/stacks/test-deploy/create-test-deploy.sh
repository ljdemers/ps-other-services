#!/usr/bin/env bash

aws cloudformation create-stack \
  --stack-name test-sis-api-deploy \
  --template-body file://sis-api-test-deploy.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM \
  --tags '[{"Key":"Environment","Value":"test"},{"Key":"Cost_Centre","Value":"Central"},{"Key":"Expiry","Value":"Never"},{"Key":"Project","Value":"SIS API Test Deployment"},{"Key":"Purpose","Value":"Deploy SIS API to TEST environment"},{"Key":"Name","Value":"test-sis-api-deploy"},{"Key":"workload-monitoring","Value":"test"}]'

