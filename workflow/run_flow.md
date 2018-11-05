# Run Flow

## Ensure Env Set

### Download Kubeflow Registry

```bash
[ -d "${KUBEFLOW_DIR}" ] && rm -rf ${KUBEFLOW_DIR}

mkdir ${${KUBEFLOW_DIR}
cd ${KUBEFLOW_DIR}
curl https://raw.githubusercontent.com/kubeflow/kubeflow/${KUBEFLOW_TAG}/scripts/download.sh | bash
```

### Init KFAPP

```bash
[ -d ${HOME}/${PROJECT}/${KFAPP} ] && rm -rf ${HOME}/${PROJECT}/${KFAPP}
cd ${HOME}/${PROJECT}

${KUBEFLOW_DIR}/scripts/kfctl.sh init ${KFAPP} --platform gcp --project ${PROJECT}
cd ${KFAPP}
```

### Apply Platform with GCFS

```bash
cd ${HOME}/${PROJECT}/${KFAPP}

. env.sh
${KUBEFLOW_DIR}/scripts/kfctl.sh generate platform
cp ${KUBEFLOW_DIR}/scripts/gke/deployment_manager_configs/gcfs.yaml gcp_config/

sed -i \
	-e 's/YOUR_DEPLOYMENT_NAME/stackoverflow-title-picker-gcfs/g' \
	-e 's/isolated-project/stackoverflow-title-picker/g' \
	-e 's/us-west1-b/us-east1-d/g' \
	gcp_config/gcfs.yaml
	
${KUBEFLOW_DIR}/scripts/kfctl.sh apply platform
# Temp issue, set RBAC and reapply
kubectl create clusterrolebinding kf-admin \
	--clusterrole=cluster-admin --user=BassManBurbank@gmail.com
${KUBEFLOW_DIR}/scripts/kfctl.sh apply platform
```

### Apply K8s Resources

```bash
${KUBEFLOW_DIR}/scripts/kfctl.sh generate k8s
${KUBEFLOW_DIR}/scripts/kfctl.sh apply k8s
```

### Configure Kubeflow to mount the Cloud Filestore volume

```bash
cd ${HOME}/${PROJECT}/${KFAPP}/ks_app
ks generate google-cloud-filestore-pv google-cloud-filestore-pv --name="claim-bassmanburbank-40gmail-2ecom" \
   --storageCapacity="${GCFS_STORAGE}" \
   --serverIP="${GCFS_INSTANCE_IP_ADDRESS}"
ks param set jupyterhub disks "claim-bassmanburbank-40gmail-2ecom"

# Check filestore instance
gcloud --project=${PROJECT} beta filestore instances list
 
cd ${HOME}/${PROJECT}/${KFAPP}
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
kubectl get pvs

# Check filestore instance
gcloud --project=${PROJECT} beta filestore instances list

# Filestore pod details
kubectl describe po/jupyter-bassmanburbank-40gmail-2ecom
```


## Clean up

```bash
${KUBEFLOW_DIR}/scripts/kfctl.sh delete all
```