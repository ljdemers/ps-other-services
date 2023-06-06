#!/usr/bin/env bash

aws cloudformation create-stack \
  --stack-name test-screening-workers-deploy \
  --template-body file://screening-workers-test-deploy.json \
  --profile polestar-test \
  --region us-east-1 \
  --capabilities=CAPABILITY_NAMED_IAM \
  --tags '[{"Key":"Environment","Value":"test"},{"Key":"Cost_Centre","Value":"Central"},{"Key":"Expiry","Value":"Never"},{"Key":"Project","Value":"Screening Workers Test Deployment"},{"Key":"Purpose","Value":"Deploy Screening Workers to TEST environment"},{"Key":"Name","Value":"test-screening-workers-deploy"},{"Key":"workload-monitoring","Value":"test"}]'
