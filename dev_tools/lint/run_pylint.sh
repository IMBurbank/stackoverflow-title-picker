#!/bin/sh

ROOT_DIR="stackoverflow-title-picker"
DOCKER_PATH="../dockerfiles"


cd $(dirname $0)

if [ "$(pwd)" = "*${ROOT_DIR}*" ]; then
	echo "Error: can't find ROOT_DIR: ${ROOT_DIR}"
	exit 1
fi

project_root="$(pwd | sed s/${ROOT_DIR}.*/${ROOT_DIR}/)"
echo "project_root: ${project_root}"

docker build \
	#--no-cache  \
	-f ${DOCKER_PATH}/pylint.Dockerfile\
	-t pylint \
	${DOCKER_PATH}

docker run \
	--rm \
	-u $(id -u):$(id -g) \
	-v ${project_root}:/workdir \
	-it \
	pylint \
	"$@"