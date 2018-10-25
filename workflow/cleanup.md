# Delete Kubeflow resources
cd ${KFAPP}
${KUBEFLOW_SRC}/scripts/kfctl.sh delete all

# To delete the cluster:
gcloud container clusters delete ${KNAME} --zone ${ZONE}