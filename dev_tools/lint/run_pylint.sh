#!/bin/sh


##### VARIABLES #####
ROOT_DIR="stackoverflow-title-picker"
DOCKER_PATH="../dockerfiles"
CMD_BASE="python -m pylint --rcfile dev_tools/lint/pylintrc"

cmd_run=""


##### FLAGS #####
file_path=""		# flag -f

while getopts ":h:f:" flag; do
	case "${flag}" in
		h) 
			echo "HELP STUB: Check CONTRIBUTING.md"
			exit 0
			;;
		f) 
			file_path="${OPTARG}"
			;;
		*) 
			echo "ERROR: Invalid flag ${flag}"
			exit 1
			;;
	esac
done
shift `expr $OPTIND - 1`


##### MAIN #####
cd $(dirname $0)

if [ "$(pwd)" = "*${ROOT_DIR}*" ]; then
	echo "Error: can't find ROOT_DIR: ${ROOT_DIR}"
	exit 1
fi

if [ -z "${file_path}" ]; then
	cmd_run="$@"
else
	cmd_run="${CMD_BASE} ${file_path}"
fi

project_root="$(pwd | sed s/${ROOT_DIR}.*/${ROOT_DIR}/)"
echo "project_root: ${project_root}"

docker build \
	-f ${DOCKER_PATH}/pylint.Dockerfile \
	-t pylint \
	${DOCKER_PATH}

echo "DOCKER RUN COMMAND (default if blank): ${cmd_run}"
docker run \
	--rm \
	-u $(id -u):$(id -g) \
	-v ${project_root}:/workdir \
	-it \
	pylint \
	${cmd_run}