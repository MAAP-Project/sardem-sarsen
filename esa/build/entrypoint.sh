#! /bin/bash

set -ex
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# ESA DPS command-line is --bbox ${BBOX} --catalog_path ${CATALOG_PATH}
# ${BBOX} : bounding box coordinate
# ${CATALOG_PATH} : path into a STAC Catalog

BBOX=$2
CATALOG_PATH=$4

# Creating output folder
outdir="/projects/data/output"
mkdir -p "${outdir}"

cd /projects

# activate dem
. /opt/conda/etc/profile.d/conda.sh
conda activate /opt/conda/envs/dem

# shellcheck disable=SC2086
python  /opt/sardem-sarsen/sardem-sarsen.py -o /projects/data/output --bbox ${BBOX} --stac_catalog_folder  ${CATALOG_PATH}

# print output dir for debug
find "${outdir}" -type f
