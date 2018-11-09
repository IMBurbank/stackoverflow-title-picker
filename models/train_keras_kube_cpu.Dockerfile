FROM python:3.6

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

RUN pip install --upgrade --no-cache-dir \
        annoy \
        bernoulli \
        bs4 \
        dill \
        google-cloud-storage \
        h5py \
        jupyter \
        keras \
        ktext \
        matplotlib \
        # Pinned ktext depencency
        msgpack-numpy==0.4.3.2 \
        nltk \
        numpy \
        pandas \
        sklearn \
        tensorboard \
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

WORKDIR /work

RUN chmod a+rwx /work \
    && mkdir /.local \
    && chmod a+rwx /.local

EXPOSE 8888

CMD ["bash", "-c", "source /etc/bash.bashrc && \
        jupyter notebook \
            --notebook-dir=/work \
            --ip 0.0.0.0 \
            --no-browser \
            --allow-root"]