#! /bin/bash

set -ex
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# NASA DPS command-line is --bbox ${BBOX} --stac_catalog_folder ${CATALOG_PATH}
# ${BBOX} : bounding box coordinate
# ${CATALOG_PATH} : path into a STAC Catalog
basedir=$( cd "$(dirname "$0")" ; pwd -P)
# Creating output folder
outdir="output"
mkdir -p "${outdir}"

# shellcheck disable=SC2068
conda run --live-stream -n dem python ${basedir}/sardem-sarsen.py $@ -o "${outdir}"

# print output dir for debug
find "${outdir}" -type f
