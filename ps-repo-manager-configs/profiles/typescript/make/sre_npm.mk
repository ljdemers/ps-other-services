help::

	@echo " == SRE NPM CMDS =="
	@echo ""
	@echo " login-sre-npm - this tells npm all @polestarglobal packages come from our repo and sets 12 hour auth token"
	@echo " clear-logins - clear all non-default npm repo settings (tokens stay in .npmrc but not used)"
	@echo ""


login-sre-npm:
	npm config set @polestarglobal:registry=https://polestar-tools-324252367609.d.codeartifact.us-east-1.amazonaws.com/npm/ps-npm/
	npm config set @polestar:registry=https://polestar-tools-324252367609.d.codeartifact.us-east-1.amazonaws.com/npm/ps-npm/
	npm config set //polestar-tools-324252367609.d.codeartifact.us-east-1.amazonaws.com/npm/ps-npm/:_authToken=${CODEARTIFACT_TOKEN} # pragma: allowlist secret - not secret


clear-logins:
	npm config delete registry; npm config delete @polestarglobal:registry
