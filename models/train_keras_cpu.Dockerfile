FROM gcr.io/kubeflow-images-public/tensorflow-1.10.1-notebook-cpu:v-base-7a84feb-864

ARG MODEL=seq_std_keras.py
ARG NOTEBOOK=train_keras_cpu.ipynb
ARG TRAIN=train_keras.py
ARG TRAINER=trainer_keras.py
ARG UTILS=utils_seq.py

ARG version=1
ENV VERSION ${version}

ARG bucket
ENV BUCKET ${bucket}

ARG nfs_name
ENV NFS_NAME=${nfs_name}

ARG nfs_ip
ENV NFS_IP=${nfs_ip}

# show python logs as they occur
ENV PYTHONUNBUFFERED=0
ENV GOOGLE_APPLICATION_CREDENTIALS "/home/jovyan/work/key.json"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
		nfs-common \
	&& pip install --upgrade --no-cache-dir \
        annoy \
        bernoulli \
        bs4 \
        dill \
        google-cloud-storage \
        h5py \
        keras \
        ktext \
        matplotlib \
        # Pinned ktext depencency
        msgpack-numpy==0.4.3.2 \
        nltk \
        # Updated per spacy dependency
        numpy \
        pandas \
        sklearn \
        # Updated/pinned per numpy compatibility
        tensorflow==1.11.0 \
        tqdm \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base
        
WORKDIR /home/jovyan

COPY so_models/${MODEL} \
        notebooks/train/${NOTEBOOK} \
        utils/${TRAIN} \
        utils/${TRAINER} \
        utils/${UTILS} \
        keys/key.json \
        ./

RUN chmod -R a+rwx /home/jovyan \
    && mv ${MODEL} model.py \
    && mv ${TRAIN} train.py \
    && mv ${TRAINER} trainer.py \
    && mv ${UTILS} utils.py \
    && mkdir data && chmod a+rwx data \
    && if [ ! -z "$(echo ${NFS_NAME})" ]; then \
    	mkdir /${NFS_NAME}; \
    	mount -o nolock ${NFS_IP}:/${NFS_NAME} /${NFS_NAME}; \
    	chmod a+rwx /${NFS_NAME}; \
    fi
