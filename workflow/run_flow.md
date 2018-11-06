# Run Flow

## Ensure Env Set

### Set OAuth

- Credentials consent screen - Authorized domains

```
so-title-picker-dev.cloud.goog
```

- Create OAuth Cliend Id Web App Credential

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

ks generate google-cloud-filestore-pv google-cloud-filestore-pv --name="ks-kubeflow-gcfs" \
   --storageCapacity="${GCFS_STORAGE}" \
   --serverIP="${GCFS_INSTANCE_IP_ADDRESS}"
ks param set jupyterhub disks "ks-kubeflow-gcfs"
 
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