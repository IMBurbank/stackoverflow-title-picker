"""
Train a stackoverflow-title-picker model

train_keras.py uses a trainer to train the model.

Read the input data from GCS in a zip file format.
--input_data_gcs_bucket and --input_data_gcs_path
    specify the location of input data.

Write the model back to GCS.
--output_model_gcs_bucket and --output_model_gcs_path
    specify the location of output.

Control the training.
--learning_rate and --sample_size
    specify the training parameters.

Check flags for a full list of parameters.

"""
import argparse
import logging
import os
import glob
import re
import shutil
import tempfile
import time
import zipfile

# pylint: disable=import-error
from google.cloud import storage

# pylint: enable=no-name-in-module


GCS_REGEX = re.compile("gs://([^/]*)(/.*)?")


def split_gcs_uri(gcs_uri):
    """
    Split a GCS URI into bucket and path.
    
    Parameters
    ----------
    gcs_uri: str
        GCS path

    Returns
    -------
    bucket: str
        Bucket URI
    path: str
        Data path in bucket

    """
    m = GCS_REGEX.match(gcs_uri)
    bucket = m.group(1)
    path = ""
    if m.group(2):
        path = m.group(2).lstrip("/")
    return bucket, path


def is_gcs_path(path):
    """
    Check if string is a Google Cloud Storage path.
    
    Parameters
    ----------
    path: str
        Input path to be checked

    Returns
    -------
    GCS_REGEX.match: bool
        Boolean value representing whether input is a GCS path

    """
    return GCS_REGEX.match(path)


def process_input_data(input_data_path):
    """
    Process the input file.

    If its a GCS file we download it to a temporary local file. We do this
    because Keras text preprocessing doesn't work with GCS.
    If its a zip file we unpack it.

    Parameters
    ----------
    input_data_path: The input

    Returns
    -------
    input_data_glob: The local csv file to process

    """
    if os.path.isdir(input_data_path):
        input_data_glob = glob.glob(input_data_path + "/*.csv")
    else:
        if is_gcs_path(input_data_path):
            # Download the input to a local
            with tempfile.NamedTemporaryFile() as hf:
                input_data = hf.name

            logging.info("Copying %s to %s", input_data_path, input_data)
            input_data_gcs_bucket, input_data_gcs_path = split_gcs_uri(
                input_data_path)

            logging.info("Download bucket %s object %s.", input_data_gcs_bucket,
                        input_data_gcs_path)
            bucket = storage.Bucket(storage.Client(), input_data_gcs_bucket)
            storage.Blob(input_data_gcs_path, bucket).download_to_filename(
                input_data)
        else:
            input_data = input_data_path

        ext = os.path.splitext(input_data)[-1]
        if ext.lower() == '.zip':
            zip_ref = zipfile.ZipFile(input_data, 'r')
            zip_ref.extractall('.')
            zip_ref.close()
            # TODO: Hardcoding the file in the Archive to use is brittle.
            # We should probably just require the input to be a CSV file.:
            csv_file = 'stackoverflow-questions.csv'
        else:
            csv_file = input_data

        input_data_glob = glob.glob(csv_file)

    return input_data_glob


def wait_for_preprocessing(preprocessed_file):
    """
    Wait for preprocessing.

    In the case of distributed training the workers need to wait for the
    preprocessing to be completed. But only the master runs preprocessing.

    Parameters
    ----------
    preprocessed_file: str
        Path to file containing preprocessed data

    Returns
    -------
    none

    """
    # TODO: Why block waiting for the file?
    # I think this is because only the master produces the npy
    # files so the other workers need to wait for the files to arrive.
    # It might be better to make preprocessing a separate job.
    # Move this code since its only needed when using
    # TF.Estimator
    while True:
        if os.path.isfile(preprocessed_file):
            break
        logging.info("Waiting for dataset")
        time.sleep(2)


def main(unparsed_args=None):
    # Parsing flags.
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--sample_size",
        type=int,
        default=200000)#2000000

    parser.add_argument(
        "--num_epochs",
        type=int,
        default=5,
        help="Number of training epochs.")

    parser.add_argument(
        "--learning_rate",
        default=0.001,
        type=float)

    parser.add_argument(
        "--input_data",
        type=str,
        default="../data/temp/input_data",
        help="The input location. Can be a GCS or local file path.")

    parser.add_argument(
        "--output_model",
        type=str,
        default="../data/temp/",
        help="The output location for the model GCS or local file path.")

    parser.add_argument(
        "--output_body_preprocessor_dpkl",
        type=str,
        default="body_pp.dpkl")

    parser.add_argument(
        "--output_title_preprocessor_dpkl",
        type=str,
        default="title_pp.dpkl")

    parser.add_argument(
        "--output_train_title_vecs_npy",
        type=str,
        default="train_title_vecs.npy")

    parser.add_argument(
        "--output_train_body_vecs_npy",
        type=str,
        default="train_body_vecs.npy")

    parser.add_argument(
        "--mode",
        type=str,
        default="keras",
        help="Whether to train using TF.estimator or Keras.")

    parser.add_argument(
        "--model_module",
        type=str,
        default="so_models.seq_std_keras",
        help="The location for the model module.")

    parser.add_argument(
        "--trainer_module",
        type=str,
        default="utils.trainer_keras",
        help="The location for the trainer module.")

    args = parser.parse_args(unparsed_args)

    logging.basicConfig(
        level=logging.INFO,
        format=('%(levelname)s|%(asctime)s'
                '|%(pathname)s|%(lineno)d| %(message)s'),
        datefmt='%Y-%m-%dT%H:%M:%S',
    )
    logging.getLogger().setLevel(logging.INFO)
    logging.info(args)

    mode = args.mode.lower()
    if not mode in ["estimator", "keras"]:
        raise ValueError(
            "Unrecognized mode %s; must be keras or estimator" % mode)

    model = __import__(args.model_module, fromlist=[None])
    trainer = __import__(args.trainer_module, fromlist=[None])

    input_data_glob = process_input_data(args.input_data)
    timestamp = int(time.time())
    output_model_name = "model-" + str(timestamp) + ".h5"


    # Use a temporary directory for all the outputs.
    # We will then copy the files to the final directory.
    output_dir = tempfile.mkdtemp()
    model_trainer = trainer.Trainer(model, output_dir)
    model_trainer.preprocess(input_data_glob, args.sample_size)

    model_trainer.build_model(args.learning_rate)

    # Tuples of (temporary, final) paths
    pairs = []

    local_model_output = args.output_model

    if is_gcs_path(args.output_model):
        local_model_output = os.path.join(output_dir, output_model_name)
    elif os.path.isdir(args.output_model):
        local_model_output = os.path.join(output_dir, output_model_name)

    model_trainer.train(
        local_model_output,
        base_name=os.path.join(output_dir, "model-checkpoint"),
        epochs=args.num_epochs)

    model_trainer.evaluate()

    # With Keras we might need to write to a local directory and then
    # copy to GCS.
    pairs.append((local_model_output, args.output_model))

    pairs.extend([
        (model_trainer.body_pp_file, args.output_body_preprocessor_dpkl),
        (model_trainer.title_pp_file, args.output_title_preprocessor_dpkl),
        (model_trainer.preprocessed_titles, args.output_train_title_vecs_npy),
        (model_trainer.preprocessed_bodies, args.output_train_body_vecs_npy),])

    # Copy outputs
    for p in pairs:
        local = p[0]
        remote = p[1]
        if local == remote:
            continue

        logging.info("Copying %s to %s", local, remote)

        if is_gcs_path(remote):
            bucket_name, path = split_gcs_uri(remote)
            bucket = storage.Bucket(storage.Client(), bucket_name)
            blob = storage.Blob(path, bucket)
            blob.upload_from_filename(local)
        else:
            shutil.move(local, remote)


if __name__ == '__main__':
    main()
