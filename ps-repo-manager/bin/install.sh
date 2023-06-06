#!/usr/bin/env bash

# Abort on nonzero exitstatus.
set -o errexit

# Don't hide errors within pipes.
set -o pipefail

# Abort on unbound variable.
set -o nounset

get_codeartifact_url() {

    local -r aws_profile="polestar-tools"
    local -r aws_account_id="324252367609"
    local -r aws_account_name="polestar-tools"
    local -r aws_region="us-east-1"
    local -r ps_python_repo_name="ps-python"

    local -r codeartifact_auth_token=$(
        aws codeartifact get-authorization-token \
            --region ${aws_region} \
            --profile ${aws_profile} \
            --domain ${aws_account_name} \
            --domain-owner ${aws_account_id} \
            --query authorizationToken \
            --output text
    )

    local codeartifact_url="https://aws:${codeartifact_auth_token}@${aws_account_name}-"
    codeartifact_url+="${aws_account_id}.d.codeartifact.${aws_region}.amazonaws.com"
    codeartifact_url+="/pypi/${ps_python_repo_name}/simple/"

    echo $codeartifact_url
}

install_ps_repo_manager() {

    local -r codeartifact_url="${1}"

    # The `--user` option is not supported in virtual environments, hence not
    # passing it in if running in a virtual environment.
    local user="" && [[ -z "${VIRTUAL_ENV:-}" ]] && user="--user"

    pip install --upgrade ${user} --extra-index-url "${codeartifact_url}" ps-repo-manager
}

main () {

    local -r codeartifact_url="$(get_codeartifact_url)"

    install_ps_repo_manager "$codeartifact_url"
}

main
