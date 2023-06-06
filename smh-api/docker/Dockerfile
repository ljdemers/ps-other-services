FROM 178847878690.dkr.ecr.us-east-1.amazonaws.com/python:3.6-slim-buster

WORKDIR /opt/smh/

COPY ./requirements.txt ./
COPY ./requirements-dev.txt ./
COPY ./dist-packages/* /opt/smh/dist-packages/

RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get clean

RUN pip install -U pip setuptools
RUN pip install -r requirements-dev.txt --find-links /opt/smh/dist-packages --no-cache-dir
