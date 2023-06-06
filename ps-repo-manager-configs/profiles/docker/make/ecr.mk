#ECR
ECR_URL_TOOLS_URL=324252367609.dkr.ecr.us-east-1.amazonaws.com
ECR_URL_TEST_URL=178847878690.dkr.ecr.us-east-1.amazonaws.com

ECR_GOVCLOUD_DSE_COMMS_DEV_URL=188867765545.dkr.ecr.us-gov-west-1.amazonaws.com
ECR_GOVCLOUD_DSE_DEVOPS_DEV_URL=188680451036.dkr.ecr.us-gov-west-1.amazonaws.com
ECR_GOVCLOUD_TMS_DEVOPS_DEV_URL=643814821573.dkr.ecr.us-gov-west-1.amazonaws.com

ecr-help:

	@echo " == AWS ECR =="
	@echo ""
	@echo " ecr-login-tools"
	@echo " ecr-login-tools-no-profile"
	@echo " ecr-login-test"
	@echo ""
	@echo " ecr-login-govcloud-dse-comms-dev"
	@echo " ecr-login-govcloud-dse-devops-dev"
	@echo " ecr-login-govcloud-tms-devops-dev"
	@echo ""

help:: ecr-help

##############################################################################

ecr-login-tools:
	aws ecr get-login-password \
		--profile $(AWS_CLI_TOOLS_PROFILE) \
		| docker login --username AWS --password-stdin $(ECR_URL_TOOLS_URL)

ecr-login-tools-no-profile:
	aws ecr get-login-password \
		| docker login --username AWS --password-stdin $(ECR_URL_TOOLS_URL)

ecr-login-test:
	aws ecr get-login-password \
		--profile $(AWS_CLI_TEST_PROFILE) \
		| docker login --username AWS --password-stdin $(ECR_URL_TEST_URL)

##############################################################################

ecr-login-govcloud-dse-comms-dev:
	aws ecr get-login-password \
		--profile $(AWS_CLI_GOVCLOUD_DSE_COMMS_DEV_PROFILE) \
		| docker login --username AWS --password-stdin $(ECR_GOVCLOUD_DSE_COMMS_DEV_URL)

ecr-login-govcloud-dse-devops-dev:
	aws ecr get-login-password \
		--profile $(AWS_CLI_GOVCLOUD_DSE_DEVOPS_DEV_PROFILE) \
		| docker login --username AWS --password-stdin $(ECR_GOVCLOUD_DSE_DEVOPS_DEV_URL)

ecr-login-govcloud-tms-devops-dev:
	aws ecr get-login-password \
		--profile $(AWS_CLI_GOVCLOUD_TMS_DEVOPS_DEV_PROFILE) \
		| docker login --username AWS --password-stdin $(ECR_GOVCLOUD_TMS_DEVOPS_DEV_URL)
