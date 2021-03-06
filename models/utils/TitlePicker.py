"""
Generates predictions using a stored model.

Uses trained model files to generate a prediction.

"""
from __future__ import print_function

import os

# pylint: disable=import-error
import numpy as np
import dill as dpickle

# pylint: disable=no-name-in-module
from keras.models import load_model
from utils.utils_seq import Inference
# pylint: enable=import-error
# pylint: enable=no-name-in-module


class TitlePicker(object):
    def __init__(self):
    """Class for TitlePicker predictions."""
        body_pp_file = os.getenv('BODY_PP_FILE', 'body_pp.dpkl')
        print('body_pp file {0}'.format(body_pp_file))
        with open(body_pp_file, 'rb') as body_file:
            body_pp = dpickle.load(body_file)

        title_pp_file = os.getenv('TITLE_PP_FILE', 'title_pp.dpkl')
        print('title_pp file {0}'.format(title_pp_file))
        with open(title_pp_file, 'rb') as title_file:
            title_pp = dpickle.load(title_file)

        model_file = os.getenv('MODEL_FILE', 'model_seq_std_keras.h5')
        print('model file {0}'.format(model_file))
        self.model = Inference(encoder_preprocessor=body_pp,
                               decoder_preprocessor=title_pp,
                               trained_model=load_model(model_file))

    def predict(self,
                input_text,
                feature_names): # pylint: disable=unused-argument
        """Predict title"""
        return np.asarray(
            [[self.model.generate_title(body[0])[1]]
             for body in input_text])
