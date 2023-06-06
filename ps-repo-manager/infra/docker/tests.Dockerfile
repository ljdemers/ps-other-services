FROM public.ecr.aws/lts/ubuntu:20.04

ARG CODEARTIFACT_TOKEN

# Some information taken from https://hub.docker.com/r/thekevjames/nox/dockerfile
# apt and global pip depends not critical for these tests
# hadolint ignore=DL3008
RUN apt-get update -y && \
    apt-get install -qy --no-install-recommends ca-certificates curl gnupg2 make && \
    rm -rf /var/cache/apt/lists

# hadolint ignore=SC1091
RUN . /etc/os-release && \
    echo "deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu ${UBUNTU_CODENAME} main" > /etc/apt/sources.list.d/deadsnakes.list && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776

# Not critical for these tests
# hadolint ignore=DL3008
RUN apt-get update -y && \

    apt-get install --no-install-recommends -y python3.6 && \
    apt-get install --no-install-recommends -y python3.6-dev && \
    apt-get install --no-install-recommends -y python3.6-distutils && \

    apt-get install --no-install-recommends -y python3.8 && \
    apt-get install --no-install-recommends -y python3.10 && \

    apt-get install --no-install-recommends -y python3-pip && \

    apt-get install --no-install-recommends -y git && \

    rm -rf /var/cache/apt/lists

# Install nox via default python
# hadolint ignore=DL3013
RUN python3.8 -m pip --no-cache-dir install poetry nox && \
    python3.6 -m pip --no-cache-dir install --upgrade pip && \
    mkdir /opt/repo-manager

COPY . /opt/repo-manager

WORKDIR /opt/repo-manager

RUN CODEARTIFACT_TOKEN=${CODEARTIFACT_TOKEN} make poetry-codeartifact-load-pass-env

WORKDIR /opt/repo-manager/repomanager/tests

CMD ["nox", "--error-on-missing-interpreters"]
