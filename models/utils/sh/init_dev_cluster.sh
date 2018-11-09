#!/bin/sh

. $(dirname $0)/dev.env.sh

# Choose & set compute zone
gcloud config set compute/zone ${ZONE}

# Set cluster variables and create
gcloud container clusters create ${KNAME} --zone ${ZONE} --machine-type ${KMACHINE}

# Connect local environment with cluster to interact with it using kubectl
gcloud container clusters get-credentials ${KNAME} --zone ${ZONE}

# Create cluster-admin role for user on cluster
kubectl create clusterrolebinding default-admin \
      --clusterrole=cluster-admin --user=$(gcloud config get-value account)
      
# Install NVIDIA drivers on Container-Optimized OS (for GPU on k8s-1.9 server)
kubectl create -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/k8s-1.9/daemonset.yaml