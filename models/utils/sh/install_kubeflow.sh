#!/bin/sh

. $(dirname $0)/dev.env.sh

# Create and enter kubeflow directory
mkdir ${KUBEFLOW_SRC}
cd ${KUBEFLOW_SRC}

# Download and run download.sh to pull kubeflow registry and utility scripts
curl https://raw.githubusercontent.com/kubeflow/kubeflow/${KUBEFLOW_TAG}/scripts/download.sh | bash