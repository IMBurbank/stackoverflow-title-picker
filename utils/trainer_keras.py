"""
Trainer for stackoverflow-title-picker model

trainer_keras.py provides a harness for the model.

"""
import json
import logging
import os
import sys

# pylint: disable=import-error
import numpy as np
import dill as dpickle
import pandas as pd
import tensorflow as tf
import keras

from keras.callbacks import CSVLogger, ModelCheckpoint
from bs4 import BeautifulSoup
from ktext.preprocess import processor
from sklearn.model_selection import train_test_split

# pylint: disable=no-name-in-module
from utils import load_decoder_inputs
from utils import load_encoder_inputs
from utils import load_text_processor
from utils import Inference
# pylint: enable=import-error
# pylint: enable=no-name-in-module


class Trainer(object): # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 model_file,
                 output_dir,
                 body_keep_n=12000,
                 title_keep_n=6000,
                 body_maxlen=250,
                 title_maxlen=12):
        """
        Construct the trainer.

        Parameters
        ----------
        model_file: module
            Module to instantiate model for training
        output_dir: str
            Directory where outputs should be written.

        """
        if not model_file:
            raise ValueError("model_file can't be None.")
        elif not output_dir:
            raise ValueError("output_dir can't be None.")

        self.model_file = model_file
        self.output_dir = output_dir
        self.body_keep_n = body_keep_n
        self.body_maxlen = body_maxlen
        self.title_keep_n = title_keep_n
        self.title_maxlen = title_maxlen

        self.tf_config = os.environ.get('TF_CONFIG', '{}')
        self.tf_config_json = json.loads(self.tf_config)

        self.job_name = self.tf_config_json.get('task', {}).get('type')

        # Files storing the preprocessors
        self.body_pp_file = os.path.join(self.output_dir, 'body_pp.dpkl')
        self.title_pp_file = os.path.join(self.output_dir, 'title_pp.dpkl')

        # Files to store the processed data
        self.preprocessed_titles = os.path.join(self.output_dir,
                                                'train_title_vecs.npy')
        self.preprocessed_bodies = os.path.join(self.output_dir,
                                                'train_body_vecs.npy')

        self.body_pp = None
        self.decoder_input_data = None
        self.decoder_target_data = None
        self.encoder_input_data = None
        self.history = None
        self.Model = None
        self.test_df = None
        self.title_pp = None

    def preprocess(self, data_file, num_samples=None):
        """
        Preprocess the input.

        Trains preprocessors and splits the data into train and test sets.

        Parameters
        ----------
        data_file: str
            The datafile to process
        num_samples: int or None
            Number of samples to use. Set to None to use entire dataset.

        """
        def strip_list_html(t_list):
            return (
                [BeautifulSoup(text, "html5lib").get_text() for text in t_list]
            )

        # We preprocess the data if we are the master or chief.
        # Or if we aren't running distributed.
        if self.job_name and self.job_name.lower() not in ["master", "chief"]:
            return

        # TODO: The test data isn't being used for anything.
        # How can we configure evaluation?
        if num_samples:
            traindf, self.test_df = train_test_split(
                pd.read_csv(data_file).sample(n=num_samples), test_size=.10)
        else:
            traindf, self.test_df = train_test_split(
                pd.read_csv(data_file), test_size=.10)

        # Print stats about the shape of the data.
        logging.info('Train: %d rows %d columns',
                     traindf.shape[0], traindf.shape[1])

        train_body_raw = traindf.body.tolist()
        train_title_raw = traindf.question_title.tolist()

        # Clean, tokenize, and apply padding / truncating such that
        # each document length = 250. Also, retain only the top 8,000 words
        # in the vocabulary andset the remaining words to 1 which will
        # become common index for rare words.
        self.body_pp = processor(keep_n=self.body_keep_n,
                                 padding_maxlen=self.body_maxlen)
        train_body_vecs = self.body_pp.fit_transform(
            strip_list_html(train_body_raw))

        logging.info('Example original body: %s', train_body_raw[0])
        logging.info('Example body after pre-processing: %s',
                     train_body_vecs[0])

        self.title_pp = processor(append_indicators=True,
                                  keep_n=self.title_keep_n,
                                  padding_maxlen=self.title_maxlen,
                                  padding='post')
        train_title_vecs = self.title_pp.fit_transform(train_title_raw)

        logging.info('Example original title: %s', train_title_raw[0])
        logging.info('Example title after pre-processing: %s',
                     train_title_vecs[0])

        # Save the preprocessor
        with open(self.body_pp_file, 'wb') as f:
            dpickle.dump(self.body_pp, f)

        with open(self.title_pp_file, 'wb') as f:
            dpickle.dump(self.title_pp, f)

        # Save the processed data
        np.save(self.preprocessed_titles, train_title_vecs)
        np.save(self.preprocessed_bodies, train_body_vecs)

    def build_model(self, learning_rate):
        """
        Build a keras model.

        Parameters
        ----------
        learning_rate: float
            Training learning rate.

        """
        logging.info("starting")

        if self.job_name and self.job_name.lower() in ["ps"]:
            logging.info("ps doesn't build model")
            return

        self.encoder_input_data, doc_length = (
            load_encoder_inputs(self.preprocessed_bodies))

        self.decoder_input_data, self.decoder_target_data = (
            load_decoder_inputs(self.preprocessed_titles))

        num_encoder_tokens, self.body_pp = load_text_processor(
            self.body_pp_file)
        num_decoder_tokens, self.title_pp = load_text_processor(
            self.title_pp_file)

        Input_model = self.model_file.Model()

        encoder_inputs, encoder_model, encoder_out = Input_model.encoder(
            doc_length, num_encoder_tokens)
        decoder_inputs, decoder_outputs = Input_model.decoder(
            encoder_out, num_decoder_tokens)

        self.Model = Input_model.encoder_decoder(
            encoder_inputs, decoder_inputs, decoder_outputs)

        # Compile model
        self.Model.compile(
            optimizer=keras.optimizers.Nadam(lr=learning_rate),
            loss='sparse_categorical_crossentropy',)
            #  TODO: Computing accuracy causes a dimension mismatch.
            # tensorflow.python.framework.errors_impl.InvalidArgumentError: Incompatible shapes: [869] vs. [79,11] # pylint: disable=line-too-long
            # [[{{node metrics/acc/Equal}} = Equal[T=DT_FLOAT, _device="/job:localhost/replica:0/task:0/device:CPU:0"](metrics/acc/Reshape, metrics/acc/Cast)]]  # pylint: disable=line-too-long
            # metrics=['accuracy'])

        self.Model.summary()

    def train(self,
              output_model_h5,
              base_name='model_def_keras',
              batch_size=1200,
              epochs=10):
        """
        Train using Keras.

        This is an alternative to using the TF.Estimator API.
        TODO: The reason we added support for using Keras
        was to debug whether we were hitting issue:
        https://github.com/keras-team/keras/issues/9761 only with TF.Estimator.

        """
        logging.info("Using base name: %s", base_name)
        csv_logger = CSVLogger('{:}.log'.format(base_name))
        model_checkpoint = ModelCheckpoint(
            '{:}.epoch{{epoch:02d}}-val{{val_loss:.5f}}.hdf5'.format(
                base_name),
            save_best_only=True)

        self.history = self.Model.fit(
            [self.encoder_input_data, self.decoder_input_data],
            np.expand_dims(self.decoder_target_data, -1),
            batch_size=batch_size,
            epochs=epochs,
            validation_split=0.12,
            callbacks=[csv_logger, model_checkpoint])

        # Save model
        self.Model.save(output_model_h5)

    def evaluate(self):
        """
        Generates predictions on holdout set and calculates BLEU Score.

        """
        inference = Inference(encoder_preprocessor=self.body_pp,
                              decoder_preprocessor=self.title_pp,
                              Model=self.Model)

        bleu_score = inference.evaluate_model(
            holdout_bodies=self.test_df.body.tolist(),
            holdout_titles=self.test_df.question_title.tolist())

        logging.info("Bleu score: %s", bleu_score)
        return bleu_score
