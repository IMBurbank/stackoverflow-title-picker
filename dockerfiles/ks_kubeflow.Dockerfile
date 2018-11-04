FROM golang:alpine


ARG KS_VER=0.12.0
ARG KS_DIST=linux_amd64
ARG KS_PKG=ks_${KS_VER}_${KS_DIST}

ARG KUBEFLOW_VERSION=0.3.1
ARG KFAPP=ks-kubeflow
ARG PROJECT=stackoverflow-title-picker
ARG PLATFORM=gcp
ARG ZONE=us-central1-a
ARG EMAIL="bassmanburbank@gmail.com"

ENV KUBEFLOW_SRC /kubeflow

RUN apk add --no-cache \
        bash \
        curl \
    ; \
    # Install ksonnet to local bin
    cd /; \
    echo ${KS_PKG}; \
    curl -Lk https://github.com/ksonnet/ksonnet/releases/download/v${KS_VER}/${KS_PKG}.tar.gz | tar -C /usr/local/bin/ -xz ${KS_PKG}/ks --strip=1 \
    ; \
    echo $(ks version); \
    # Create kubeflow install directory
    mkdir ${KUBEFLOW_SRC}; \
    chmod a+rwx ${KUBEFLOW_SRC}; \
    cd ${KUBEFLOW_SRC}/; \
    # Download kubeflow
    curl -Lk https://github.com/kubeflow/kubeflow/archive/v${KUBEFLOW_VERSION}.tar.gz | tar -xz kubeflow-${KUBEFLOW_VERSION}/scripts/ kubeflow-${KUBEFLOW_VERSION}/kubeflow/ --strip=1 \
    ; \
    # Create kfapp
    ${KUBEFLOW_SRC}/scripts/kfctl.sh init ${KFAPP} \
        --platform ${PLATFORM} \
        --project ${PROJECT} \
    ;
    # Generate and apply kubeflow components to cluster
    #cd ${KFAPP}; \
    #${KUBEFLOW_SRC}/scripts/kfctl.sh generate platform; \
    #${KUBEFLOW_SRC}/scripts/kfctl.sh apply platform; \
    #${KUBEFLOW_SRC}/scripts/kfctl.sh generate k8s; \
    #${KUBEFLOW_SRC}/scripts/kfctl.sh apply k8s;

WORKDIR /my-devel

EXPOSE 8000
EXPOSE 8080
EXPOSE 8888