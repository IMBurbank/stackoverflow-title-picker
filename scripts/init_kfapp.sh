#!/bin/sh

. $(dirname $0)/dev.env.sh

# Change to project directory
cd $HOME/${PROJ_NAME}/

# Run the following commands to setup and deploy Kubeflow

# Create and change to KFAPP
${KUBEFLOW_SRC}/scripts/kfctl.sh init ${KFAPP} --platform gcp
cd ${KFAPP}

# Generate and apply kubeflow components to cluster
${KUBEFLOW_SRC}/scripts/kfctl.sh generate k8s
${KUBEFLOW_SRC}/scripts/kfctl.sh apply k8s