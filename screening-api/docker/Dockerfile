FROM 178847878690.dkr.ecr.us-east-1.amazonaws.com/python:3.6-alpine3.10 as base

RUN apk --update upgrade && \
    apk add alpine-sdk bash make curl python3-dev git openssh postgresql-dev \
        gcc musl-dev libffi-dev zlib-dev jpeg-dev tiff-dev libxml2-dev \
        libxslt-dev cairo-dev pango-dev linux-headers && \
    rm -rf /var/cache/apk/*

# Surpress error: Can not find Rust compiler
ENV CRYPTOGRAPHY_DONT_BUILD_RUST 1

# A variable to be used during build time to populate CodeArtifact token
ARG CODEARTIFACT_AUTH_TOKEN
#RUN pip config set global.index-url "https://aws:$CODEARTIFACT_AUTH_TOKEN@test-domain-178847878690.d.codeartifact.us-east-1.amazonaws.com/pypi/polestar-pypi-store/simple/"
RUN pip config set global.extra-index-url "https://pypi.org/simple"
 
COPY pre-requirements.txt .
RUN python3 -m pip install -r pre-requirements.txt

COPY dependency_links.txt requirements.txt ./
RUN pip install --prefer-binary -r dependency_links.txt -r requirements.txt

COPY requirements_dev.txt .
RUN pip install --prefer-binary -r requirements_dev.txt

FROM base as build

RUN pip install --upgrade twine wheel

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN python setup.py bdist_wheel --dist-dir=/

FROM base as prod

RUN mkdir -p /var/log/polestar/screening

ENV TERM linux
ENV TERMINFO /etc/terminfo

COPY --from=build /*.whl .
RUN pip install *.whl

EXPOSE 80

ENTRYPOINT ["/usr/local/bin/gunicorn"]
CMD ["-b", "0.0.0.0:80", "--worker-class", "gevent", "--workers", "3", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "screening_api.wsgi:app", "--log-level", "info"]

FROM base as dev

COPY ./docker/entrypoint.sh /usr/bin/entrypoint
RUN chmod 755 /usr/bin/entrypoint

RUN mkdir -p /var/log/app

RUN mkdir -p /tmp/wheelhouse

ENV TERM linux
ENV TERMINFO /etc/terminfo

WORKDIR /usr/src/app

ENTRYPOINT ["entrypoint"]
