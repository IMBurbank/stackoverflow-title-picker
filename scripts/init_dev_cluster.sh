#!/bin/sh

. $(dirname $0)/dev.env.sh

# Choose & set compute zone
gcloud config set compute/zone ${ZONE}

# Set cluster variables and create
gcloud container clusters create ${KNAME} --zone ${ZONE} --machine-type ${KMACHINE}

# Connect our local environment to the cluster 
# so we can interact with it locally using the Kubernetes CLI tool, kubectl:
gcloud container clusters get-credentials ${KNAME} --zone ${ZONE}

# Create cluster-admin role for user on cluster
kubectl create clusterrolebinding default-admin \
      --clusterrole=cluster-admin --user=$(gcloud config get-value account)
      
# Install NVIDIA drivers on Container-Optimized OS:
kubectl create -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/k8s-1.9/daemonset.yaml