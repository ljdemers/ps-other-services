#!/bin/bash

set -eux -o pipefail

# health
python -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. grpc/health/v1/*.proto
rm -f grpc_health_v1/*.pb.py
cp grpc/health/v1/*_pb2.py grpc_health_v1/
cp grpc/health/v1/*_pb2_grpc.py grpc_health_v1/

# portservice
python -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. grpc/portservice/v1/*.proto
rm -f grpc_portservice_v1/*.pb.py
cp grpc/portservice/v1/*_pb2.py grpc_portservice_v1/
cp grpc/portservice/v1/*_pb2_grpc.py grpc_portservice_v1/
