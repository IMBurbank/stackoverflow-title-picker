FROM python:3.6

ARG MODEL=seq_std_keras.py
ARG TRAIN=train_keras.py
ARG TRAINER=trainer_keras.py
ARG UTILS=utils_seq.py

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y \
        unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade --no-cache-dir \
        annoy \
        bs4 \
        dill \
        google-cloud-storage \
        h5py \
        keras \
        ktext \
        nltk \
        numpy \
        matplotlib \
        sklearn \
        tensorflow \
        tqdm

WORKDIR /my-work

COPY models/${MODEL} \
        utils/${TRAIN} \
        utils/${TRAINER} \
        utils/${UTILS} \
        utils/sh/download_data.py \
        deployment/gke/distributed \
        ./

RUN chmod -R a+rwx /my-work \
    && mv /my-work/${MODEL} /my-work/model.py \
    && mv /my-work/${TRAIN} /my-work/train.py \
    && mv /my-work/${TRAINER} /my-work/trainer.py \
    && mv /my-work/${UTILS} /my-work/utils.py \
    && mkdir /model && chmod a+rwx /model \
    && mkdir /data && chmod a+rwx /data

CMD python train.py
