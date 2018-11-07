#!/usr/bin/env bash

CONTEXT="$(dirname $0)/../dockerfiles"

docker build -f ${CONTEXT}/dev-gpu.Dockerfile -t tf-dev ${CONTEXT}/
