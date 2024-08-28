#! /bin/bash

set -ex
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# NASA DPS command-line is --bbox ${BBOX} --stac_catalog_folder ${CATALOG_PATH}
# ${BBOX} : bounding box coordinate
# ${CATALOG_PATH} : path into a STAC Catalog

# Creating output folder
outdir="output"
mkdir -p "${outdir}"

# shellcheck disable=SC2068
conda run --live-stream -n dem python /app/sardem-sarsen/sardem-sarsen.py $@ -o "${outdir}"

# print output dir for debug
find "${outdir}" -type f
