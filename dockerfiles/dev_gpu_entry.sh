#!/usr/bin/env bash
# Entry point into container
# Load environmental variables before container commands

set -a
. /etc/bash.bashrc >/dev/null
set +a

exec "$@"