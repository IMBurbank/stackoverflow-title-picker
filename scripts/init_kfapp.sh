#!/bin/sh

. $(dirname $0)/dev.env.sh

# Change to project directory
cd $HOME/${PROJECT}/

# Run the following commands to setup and deploy Kubeflow

# Create and change to KFAPP
${KUBEFLOW_SRC}/scripts/kfctl.sh init ${KFAPP} --platform gcp --project ${PROJECT}
cd ${KFAPP}

# Generate and apply kubeflow components to cluster
${KUBEFLOW_SRC}/scripts/kfctl.sh generate platform
${KUBEFLOW_SRC}/scripts/kfctl.sh apply platform
${KUBEFLOW_SRC}/scripts/kfctl.sh generate k8s
${KUBEFLOW_SRC}/scripts/kfctl.sh apply k8s