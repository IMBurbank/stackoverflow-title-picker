#!/usr/bin/env bash

docker run \
--rm \
--runtime=nvidia \
-u $(id -u):$(id -g) \
-v $(pwd):/my-devel \
-p 8888:8888 \
-it \
tf-dev "$@"