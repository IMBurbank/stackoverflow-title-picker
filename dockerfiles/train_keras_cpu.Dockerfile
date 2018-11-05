FROM python:3.6

ARG MODEL=seq_std_keras.py
ARG NOTEBOOK=train_keras_cpu.ipynb
ARG TRAIN=train_keras.py
ARG TRAINER=trainer_keras.py
ARG UTILS=utils_seq.py

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python-pandas \
        unzip \
    && apt-get clean \
    && pip install --upgrade --no-cache-dir \
        annoy \
        bernoulli \
        bs4 \
        dill \
        google-cloud-storage \
        h5py \
        IPython \
        ipdb \
        keras \
        ktext \
        nltk \
        numpy \
        matplotlib \
        msgpack-numpy==0.4.3.2 \
        setuptools==39.1.0 \
        sklearn \
        tensorflow \
        tqdm \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

WORKDIR /workdir
EXPOSE 8000
EXPOSE 8080
EXPOSE 8888

COPY models/${MODEL} \
        notebooks/train/${NOTEBOOK} \
        utils/${TRAIN} \
        utils/${TRAINER} \
        utils/${UTILS} \
        ./

RUN chmod -R a+rwx /workdir \
    && mv /workdir/${MODEL} /workdir/model.py \
    && mv /workdir/${TRAIN} /workdir/train.py \
    && mv /workdir/${TRAINER} /workdir/trainer.py \
    && mv /workdir/${UTILS} /workdir/utils.py \
    && mkdir /model && chmod a+rwx /model \
    && mkdir /data && chmod a+rwx /data

