#!/bin/bash
#
# Script to download the data
# Usage
# download_data.sh <URL of data> <data_dir>
# e.g
# download_data.sh https://console.cloud.google.com/storage/browser/so-title-picker-data /data
#
# Script expects data to be a zip file
set -ex

URL=$1
DATA_DIR=$2


mkdir -p ${DATA_DIR}

wget --directory-prefix=${DATA_DIR} ${URL} 
TARGET=$(basename ${URL})
unzip -d ${DATA_DIR} ${DATA_DIR}/${TARGET}
