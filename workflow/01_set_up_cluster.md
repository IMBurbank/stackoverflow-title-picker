# Set Up Cluster on Google Cloud

Create project

### Set Project Variables

```bash
export PROJECT=$(gcloud config get-value project)
```

## Start GKE Cluster

### Start Cluster

```bash
# (Optional) list compute zones
gcloud compute zones list

# Choose & set compute zone-
export ZONE=us-central1-a
gcloud config set compute/zone ${ZONE}

# Set cluster variables
export KNAME=kubeflow-dev
KMACHINE=n1-standard-2

# Create
gcloud container clusters create ${KNAME} --zone ${ZONE} --machine-type ${KMACHINE}

# Connect local environment with cluster to interact with it using kubectl
gcloud container clusters get-credentials ${KNAME} --zone ${ZONE}

# Create cluster-admin role for user on cluster
kubectl create clusterrolebinding default-admin \
      --clusterrole=cluster-admin --user=$(gcloud config get-value account)
      
# Install NVIDIA drivers on Container-Optimized OS (for GPU)
kubectl create -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/k8s-1.9/daemonset.yaml
```

### Create oauth client credentials

Set up per [kubeflow instructions](https://www.kubeflow.org/docs/started/getting-started-gke/)

- Configure the oauth [consent](https://console.cloud.google.com/apis/credentials/consent)

- Configure oauth [credentials](https://console.cloud.google.com/apis/credentials)

- Create (make note of client ID and client secret)

- Export client ID and client secret

```bash
export CLIENT_ID=<CLIENT_ID from OAuth page>
export CLIENT_SECRET=<CLIENT_SECRET from OAuth page>
```

## Deploy Kubeflow to Cluster

### Prepare Local Cloud Environment

```bash
# Add github token to shell environmen
export GITHUB_TOKEN=<your_token_here>


# Create `bin` directory in $HOME
mkdir -p ${HOME}/bin
export PATH=$PATH:${HOME}/bin/
echo "export PATH=$PATH:${HOME}/bin/" >> .bashrc
```

Enable [IAM API](https://console.developers.google.com/apis/api/iam.googleapis.com/overview)

### Install Ksonnet

```bash
# Select KS package
KS_VER=0.12.0
KS_DIST=linux_amd64
export KS_PKG=ks_${KS_VER}_${KS_DIST}

# Download Ksonnet executable into ~/bin/
curl -Lk https://github.com/ksonnet/ksonnet/releases/download/v${KS_VER}/${KS_PKG}.tar.gz \
	| tar xzv -C $HOME/bin/ ${KS_PKG}/ks --strip=1 
```

### Install Kubeflow Registry and Scripts

```bash
# Create KF source dir and enter
export KUBEFLOW_SRC=${HOME}/kubeflow
export KUBEFLOW_TAG=v0.3.1
mkdir ${KUBEFLOW_SRC}
cd ${KUBEFLOW_SRC}

# Download and run download.sh to pull kubeflow registry and utility scripts
curl https://raw.githubusercontent.com/kubeflow/kubeflow/${KUBEFLOW_TAG}/scripts/download.sh | bash

```

### Init KS and KF using `kfctl`

Run the following commands to setup and deploy Kubeflow

```bash
# Create and change to KFAPP
${KUBEFLOW_SRC}/scripts/kfctl.sh init ${KFAPP} --platform gcp --project ${PROJECT}
cd ${KFAPP}

# Generate and apply kubeflow components to cluster
${KUBEFLOW_SRC}/scripts/kfctl.sh generate platform
${KUBEFLOW_SRC}/scripts/kfctl.sh apply platform
${KUBEFLOW_SRC}/scripts/kfctl.sh generate 
${KUBEFLOW_SRC}/scripts/kfctl.sh apply k8s
```