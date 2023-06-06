
FROM python:3.6-alpine3.10 as base
LABEL maintainer="Artur Maciag <maciag.artur@gmail.com>"

RUN apk --update upgrade && \
    apk add alpine-sdk bash curl python3-dev git openssh postgresql-dev \
        gcc g++ musl-dev libffi-dev zlib-dev jpeg-dev tiff-dev libxml2-dev \
        libxslt-dev cairo-dev pango-dev linux-headers && \
    rm -rf /var/cache/apk/*

# Surpress error: Can not find Rust compiler
ENV CRYPTOGRAPHY_DONT_BUILD_RUST 1

# A variable to be used during build time to populate CodeArtifact token
ARG CODEARTIFACT_AUTH_TOKEN
#RUN pip config set global.index-url "https://aws:$CODEARTIFACT_AUTH_TOKEN@test-domain-178847878690.d.codeartifact.us-east-1.amazonaws.com/pypi/polestar-pypi-store/simple/"
RUN pip config set global.extra-index-url "https://pypi.org/simple"

COPY requirements.txt .
RUN pip install --prefer-binary -r requirements.txt

COPY requirements_dev.txt .
RUN pip install --prefer-binary -r requirements_dev.txt

FROM base as build

RUN pip install --upgrade twine wheel

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN python setup.py bdist_wheel --dist-dir=/

ENTRYPOINT ["entrypoint"]

FROM base as prod

RUN mkdir -p /var/log/polestar/screening
RUN mkdir -p /var/run/polestar/screening

ENV TERM linux
ENV TERMINFO /etc/terminfo
ENV PIP_EXTRA_INDEX_URL https://polestar:Polestar1@pypi.polestar-testing.com/simple

COPY --from=build /*.whl .
RUN pip install *.whl

ENTRYPOINT ["celery"]
CMD ["worker", "-A", "screening_workers", "-l", "debug"]

FROM base as dev

COPY ./docker/entrypoint.sh /usr/bin/entrypoint
RUN chmod 755 /usr/bin/entrypoint

RUN mkdir -p /var/log/app
RUN mkdir -p /var/run/polestar/screening

RUN mkdir -p /tmp/wheelhouse

ENV TERM linux
ENV TERMINFO /etc/terminfo

WORKDIR /usr/src/app

ENTRYPOINT ["entrypoint"]
CMD ["celery", "worker", "-A", "screening_workers", "-l", "debug"]
