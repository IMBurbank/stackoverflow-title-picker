"""
Standard sequence-to-sequence model using keras.

seq_std_keras.py provides an instantiable model.

"""
import keras # pylint: disable=import-error


class Model(object):
    def __init__(self, latent_dim=300, model_name="Sequence - Std - Keras"):
        """
        Construct encoder-decoder model.

        Parameters
        ----------
        latent_dim: Latent dimension for embedding and hidden units
        model_name: Name of model instance.

        """
        self.latent_dim = latent_dim
        self.model_name = model_name

    def encoder(self, doc_length, num_encoder_tokens):
        """
        Build encoder model.

        Parameters
        ----------
        fname: str
            file name of ktext.proccessor object

        Returns
        -------
        num_tokens : int
            size of vocabulary loaded into ktext.processor
        pp : ktext.processor
            the processor you are trying to load

        Typical Usage:
        -------------
        num_decoder_tokens, title_pp = load_text_processor(
            fname='title_pp.dpkl')
        num_encoder_tokens, body_pp = load_text_processor(fname='body_pp.dpkl')

        """
        self.doc_length = doc_length

        latent_dim = self.latent_dim
        encoder_inputs = keras.layers.Input(shape=(doc_length,),
                                            name='Encoder-Input')

        # Word embeding for encoder (ex: Question Body)
        x = keras.layers.Embedding(num_encoder_tokens,
                                   latent_dim,
                                   name='Body-Word-Embedding',
                                   mask_zero=False)(encoder_inputs)
        x = keras.layers.BatchNormalization(name='Encoder-Batchnorm-1')(x)

        # We do not need the `encoder_output` just the hidden state.
        _, state_h = keras.layers.GRU(latent_dim,
                                      return_state=True,
                                      name='Encoder-Last-GRU')(x)

        # Encapsulate the encoder as a separate entity so we can just
        #  encode without decoding if we want to.
        encoder_model = keras.Model(inputs=encoder_inputs,
                                    outputs=state_h,
                                    name='Encoder-Model')
        encoder_out = encoder_model(encoder_inputs)

        return encoder_inputs, encoder_model, encoder_out

    def decoder(self, encoder_out, num_decoder_tokens):
        """
        Build decoder model.

        Parameters
        ----------
        fname: str
            file name of ktext.proccessor object

        Returns
        -------
        num_tokens : int
            size of vocabulary loaded into ktext.processor
        pp : ktext.processor
            the processor you are trying to load

        Typical Usage:
        -------------

        num_decoder_tokens, title_pp = load_text_processor(
            fname='title_pp.dpkl')
        num_encoder_tokens, body_pp = load_text_processor(fname='body_pp.dpkl')

        """
        latent_dim = self.latent_dim

        # for teacher forcing
        decoder_inputs = keras.layers.Input(shape=(None,),
                                            name='Decoder-Input')
        # Word Embedding For Decoder (ex: Question Titles)
        dec_emb = keras.layers.Embedding(num_decoder_tokens,
                                         latent_dim,
                                         name='Decoder-Word-Embedding',
                                         mask_zero=False)(decoder_inputs)
        dec_bn = keras.layers.BatchNormalization(
            name='Decoder-Batchnorm-1')(dec_emb)

        decoder_gru = keras.layers.GRU(latent_dim,
                                       return_state=True,
                                       return_sequences=True,
                                       name='Decoder-GRU')

        decoder_gru_output, _ = decoder_gru(dec_bn,
                                            initial_state=[encoder_out])
        x = keras.layers.BatchNormalization(
            name='Decoder-Batchnorm-2')(decoder_gru_output)

        # Dense layer for prediction
        decoder_dense = keras.layers.Dense(num_decoder_tokens,
                                           activation='softmax',
                                           name='Final-Output-Dense')
        decoder_outputs = decoder_dense(x)

        return decoder_inputs, decoder_outputs

    def encoder_decoder(self, encoder_inputs, decoder_inputs, decoder_outputs):
        """
        Build encoder-decoder model.

        Parameters
        ----------
        fname: str
            file name of ktext.proccessor object

        Returns
        -------
        num_tokens : int
            size of vocabulary loaded into ktext.processor
        pp : ktext.processor
            the processor you are trying to load

        Typical Usage:
        -------------

        num_decoder_tokens, title_pp = load_text_processor(
            fname='title_pp.dpkl')
        num_encoder_tokens, body_pp = load_text_processor(fname='body_pp.dpkl')

        """
        encoder_decoder_model = keras.Model([encoder_inputs, decoder_inputs],
                                            decoder_outputs)

        return encoder_decoder_model
