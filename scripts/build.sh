#!/bin/bash
set -e

figlet Build

# Get the directory that this script is in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}"/../scripts/load-env.sh
BINARIES_OUTPUT_PATH="${DIR}/../artifacts/build/"
WEBAPP_ROOT_PATH="${DIR}/..//app/frontend"
FUNCTIONS_ROOT_PATH="${DIR}/../functions"

# reset the current directory on exit using a trap so that the directory is reset even on error
#function finish {
#  popd > /dev/null
#}
#trap finish EXIT

# Clean previous runs on a dev machine
rm -rf ${BINARIES_OUTPUT_PATH} && mkdir -p ${BINARIES_OUTPUT_PATH}

#Build the AzLib that contains the JavaScript functions that enable the upload feature
cd app/frontend
npm install
npm run build


# zip the webapp content from app/backend to the ./artifacts folders
cd ../backend
zip -r ${BINARIES_OUTPUT_PATH}/webapp.zip .
cd $DIR

# Build the Azure Functions
cd ${FUNCTIONS_ROOT_PATH}
zip -r ${BINARIES_OUTPUT_PATH}/functions.zip .