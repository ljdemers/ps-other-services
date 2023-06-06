CODEARTIFACT_TOKEN_LOCAL_CREDS=$(shell aws codeartifact get-authorization-token --region ${AWS_DEFAULT_REGION} --domain ${AWS_CLI_TOOLS_PROFILE} --domain-owner ${AWS_CLI_TOOLS_ID} --query authorizationToken --output text --profile ${AWS_CLI_TOOLS_PROFILE})

CODEARTIFACT_TOKEN_ASSUME_CREDS=$(shell aws codeartifact get-authorization-token --domain ${AWS_CLI_TOOLS_PROFILE} --domain-owner ${AWS_CLI_TOOLS_ID} --query authorizationToken --output text)

# Default to local creds if env not passed in
CODEARTIFACT_TOKEN?=${CODEARTIFACT_TOKEN_LOCAL_CREDS}

help::

	@echo " === CODEARTIFACT CMDS ==="
	@echo " get-codeartifact-token"
	@echo ""


get-codeartifact-token:
	@echo ${CODEARTIFACT_TOKEN_LOCAL_CREDS}
