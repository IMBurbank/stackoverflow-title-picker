# Set Up Cluster on Google Cloud

Create project

### Start Cluster

```bash
# (Optional) list compute zones
gcloud compute zones list

# Choose & set compute zone
export ZONE=us-central1-a
gcloud config set compute/zone ${ZONE}

# Set cluster variables and create
export KNAME=kubeflow-dev
export KMACHINE=n1-standard-2
gcloud container clusters create ${KNAME} --zone ${ZONE} --machine-type ${KMACHINE}

# Connect our local environment to the cluster 
# so we can interact with it locally using the Kubernetes CLI tool, kubectl:
gcloud container clusters get-credentials ${KNAME} # --zone ${ZONE}

# Create cluster-admin role for user on cluster
kubectl create clusterrolebinding default-admin \
      --clusterrole=cluster-admin --user=$(gcloud config get-value account)


```

### Install Ksonnet



### Install Kubeflow


### Apply prototypes to cluster

```bash
export KF_NAMESPACE=kf-dev
kubectl create namespace ${KF_NAMESPACE}
```