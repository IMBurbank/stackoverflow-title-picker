# Run Flow

## Ensure Env Set

### Set OAuth

- Credentials consent screen - Authorized domains

```
so-title-picker-dev.cloud.goog
```

- Create OAuth Client Id Web App Credential

```
https://ks-kubeflow.endpoints.so-title-picker-dev.cloud.goog/_gcp_gatekeeper/authenticate
```

### Download Ksonnet

```bash
# Create ~/bin if it doesn't exist
[ ! -d "${HOME}/bin" ] && mkdir -p ${HOME}/bin
[ -e "${HOME}/bin/ks" ] && rm "${HOME}/bin/ks"
[ -z "$( echo ${PATH} | grep ${HOME}/bin )" ] && export PATH=$PATH:${HOME}/bin

# Download Ksonnet executable into ~/bin/
curl -Lk https://github.com/ksonnet/ksonnet/releases/download/v${KS_VER}/${KS_PKG}.tar.gz \
	| tar xzv -C $HOME/bin/ ${KS_PKG}/ks --strip=1
	
# Check
ks version
```

### Install Needed Dependencies

```bash
pip install pyyaml --user
```

### Download Kubeflow Registry

```bash
[ -d "${KUBEFLOW_DIR}" ] && rm -rf ${KUBEFLOW_DIR}

mkdir ${KUBEFLOW_DIR}
cd ${KUBEFLOW_DIR}
curl https://raw.githubusercontent.com/kubeflow/kubeflow/${KUBEFLOW_TAG}/scripts/download.sh | bash
```

### Init KFAPP

```bash
[ -d ${PROJECT_DIR}/${KFAPP} ] && rm -rf ${PROJECT_DIR}/${KFAPP}
cd ${PROJECT_DIR} && ls

${KUBEFLOW_DIR}/scripts/kfctl.sh init ${KFAPP} --platform gcp --project ${PROJECT}
cd ${KFAPP}
```

### Apply Platform with GCFS

```bash
cd ${PROJECT_DIR}/${KFAPP}

${KUBEFLOW_DIR}/scripts/kfctl.sh generate platform

# Set GCFS Storage Capacity
export GCFS_STORAGE=1024

cp ${KUBEFLOW_DIR}/scripts/gke/deployment_manager_configs/gcfs.yaml gcp_config/

sed -ri \
	-e 's/isolated-project/'"${PROJECT}"'/g' \
	-e 's/us-west1-b/'"${ZONE}"'/g' \
	-e 's/^(\s*instanceId:)\s(.*)/\1 '"${PROJECT}"'-gcfs/g' \
	-e 's/^(\s*capacityGb:)\s(.*)/\1 '"${GCFS_STORAGE}"'/g' \
	gcp_config/gcfs.yaml
	
${KUBEFLOW_DIR}/scripts/kfctl.sh apply platform

### FIXED: SKIP - (# Temp issue, set RBAC and reapply)
#kubectl create clusterrolebinding kf-admin \
#	--clusterrole=cluster-admin --user=$(gcloud config get-value account)
#${KUBEFLOW_DIR}/scripts/kfctl.sh apply platform
```

### Apply K8s Resources

```bash
${KUBEFLOW_DIR}/scripts/kfctl.sh generate k8s
${KUBEFLOW_DIR}/scripts/kfctl.sh apply k8s
```

### Configure Kubeflow to mount the Cloud Filestore volume

```bash
cd ${PROJECT_DIR}/${KFAPP}
. env.sh
cd ks_app

# Check filestore instance
gcloud --project=${PROJECT} beta filestore instances list

# Copy IP Address
export GCFS_INSTANCE_IP_ADDRESS=<ip_address> # Paste IP_ADDRESS

ks generate google-cloud-filestore-pv google-cloud-filestore-pv --name="kubeflow" \
   --storageCapacity="${GCFS_STORAGE}" \
   --serverIP="${GCFS_INSTANCE_IP_ADDRESS}"
ks param set jupyterhub disks "kubeflow"
 
cd ${PROJECT_DIR}/${KFAPP}
${KUBEFLOW_REPO}/scripts/kfctl.sh apply k8s

# Delete tf-hub-0 to allow it to bind to fs on restart
kubectl delete pod tf-hub-0 -n ${K8S_NAMESPACE}
```

### Check Resources

```bash
# Pods
kubectl get po

# Project Namesplace
kubectl -n kubeflow get all

# Persistent volume and claim
kubectl get pv
kubectl get pvc

# Storage classes
kubectl get storageclass

# Check filestore instance
gcloud --project=${PROJECT} beta filestore instances list

# Filestore pod details
kubectl describe po/jupyter-isaacmburbank-40gmail-2ecom
```

## Run Setup

### Copy Cloud Storage Service Account Key

```bash
gcloud iam service-accounts keys create ${PROJECT_DIR}/models/keys/key.json \
  --iam-account ${DEPLOYMENT_NAME}-user@${PROJECT}.iam.gserviceaccount.com
```

### Build training Docker Image and push to gcr

```bash

export DOCKERFILE=train_keras_cpu.Dockerfile
export BUCKET_NAME=test-bucket
export NFS_NAME=test-nfs
export VERSION_TAG=$(date +%s)
export TRAIN_IMG_PATH=gcr.io/${PROJECT}/${DEPLOYMENT_NAME}-train:${VERSION_TAG}

# Ensure nfs_name and nfs_ip set
export GCFS_FILESHARE_NAME=kubeflow
export GCFS_INSTANCE_IP_ADDRESS=10.83.40.74

docker build -f ${PROJECT_DIR}/models/${DOCKERFILE} \
	-t ${TRAIN_IMG_PATH} \
  --build-arg version=${VERSION_TAG} \
  --build-arg bucket=${BUCKET_NAME} \
  --build-arg nfs_name=${GCFS_FILESHARE_NAME} \
  --build-arg nfs_ip=${GCFS_INSTANCE_IP_ADDRESS} \
  ${PROJECT_DIR}/models/

docker push ${TRAIN_IMG_PATH}

```

## Deploy to Serving to Cluster

### Wrap Model For Deploy With Seldon

```bash
# Create build folder with wrapped model using hosted seldon image
cd ${PROJECT_DIR}/models
docker run -v $(pwd):/my_model seldonio/core-python-wrapper:0.7 /my_model TitlePicker 0.1 gcr.io --base-image=python:3.6 --image-name=so-title-picker-dev/title-picker

# Build and push model docker image
cd build
docker build --force-rm=true -t gcr.io/so-title-picker-dev/title-picker:0.1 .
docker push gcr.io/so-title-picker-dev/title-picker:0.1
```

### Deploy to Cluster

```bash
cd ${PROJECT_DIR}/${KFAPP}
. env
cd ks_app
# Gives cluster-admin role to the default service account in the ${NAMESPACE}
kubectl create clusterrolebinding seldon-admin --clusterrole=cluster-admin --serviceaccount=${NAMESPACE}:default
# Install the kubeflow/seldon package
ks pkg install kubeflow/seldon
# Generate the seldon component and deploy it
ks generate seldon seldon --name=seldon --namespace=${NAMESPACE}
ks apply default -c seldon


ks generate seldon-serve-simple-v1alpha2 title-picker-model-serving \
  --name=title-picker \
  --image=gcr.io/so-title-picker-dev/title-picker:0.1 \
  --replicas=2
ks apply default -c title-picker-model-serving
```

### Use Endpoint

```bash
kubectl port-forward $(kubectl get pods -n ${NAMESPACE} -l service=ambassador -o jsonpath='{.items[0].metadata.name}') -n ${NAMESPACE} 8080:80

#Using Kubernetes
curl -X POST -H 'Content-Type: application/json' -d '{"data":{"ndarray":[["How to add a new property to disable detection of image stream files those ended with -is.yml from target directory. expected behaviour by default cube should not process image stream files if user does not set it. current behaviour cube always try to execute -is.yml files which can cause some problems in most of cases, for example if you are using kuberentes instead of openshift or if you use together fabric8 maven plugin with cube"]]}}' http://localhost:8080/seldon/title-picker/api/v0.1/predictions

# Using flask
curl -X POST -H 'Content-Type: application/json' -d '{"data":{"ndarray":[["How to add a new property to disable detection of image stream files those ended with -is.yml from target directory. expected behaviour by default cube should not process image stream files if user does not set it. current behaviour cube always try to execute -is.yml files which can cause some problems in most of cases, for example if you are using kuberentes instead of openshift or if you use together fabric8 maven plugin with cube"]]}}' http://localhost:5000/predict
```


## Clean up

```bash
cd ${PROJECT_DIR}/${KFAPP}
${KUBEFLOW_DIR}/scripts/kfctl.sh delete all

# Delete IAM bindings
export DIR=$KUBEFLOW_DIR/scripts/gke
python "${DIR}/iam_patch.py" --action=remove \
  --project=${PROJECT} \
  --iam_bindings_file="${PROJECT_DIR}/${KFAPP}/gcp_config/iam_bindings.yaml"
python "${DIR}/iam_patch.py" --action=add  \
  --project=${PROJECT} \
  --iam_bindings_file="${PROJECT_DIR}/${KFAPP}/gcp_config/iam_bindings.yaml"
```