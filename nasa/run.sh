#!/usr/bin/env bash

set -xeou pipefail

# This is intended for running DPS jobs.

# `bbox` is expected to be 4 space-separated coords: left bottom right top
bbox=$1
# `compute` is optional, but any non-empty value will be converted to `--compute`
compute=${2:+--compute}

# path to the base of this repo (one level up from this script)
basedir=$(dirname "$(dirname "$(readlink -f "$0")")")

# Per NASA MAAP DPS convention, all outputs MUST be written under a directory
# named 'output' relative to the current working directory.  Once the DPS job
# finishes, MAAP will copy everything from 'output' to a directory under
# 'my-private-bucket/dps_output'. Everything else on the instance will be lost.
outdir="${PWD}/output"

# - The environment.yaml file sets up a custom conda environment called `dem`,
#   so we use `conda run` to run the script in that environment.
# - Use `scalene` to profile the script and write the output to `profile.json`.
# - The `---` is a separator to pass arguments to `sardem-sarsen.py`, not to `scalene`.
# - Disable ShellCheck SC2086 because we want to pass the arguments unquoted to
#   correctly specify inputs to `sardem-sarsen.py`, but ShellCheck will flag unquoted
#   substitutions as problematic.  For example, we want to pass arguments like
#   this:
#
#     sardem-sarsen.py --bbox -156 18.8 -154.7 20.3 --out_dir /path/to/output
#
#   and not like this:
#
#     sardem-sarsen.py --bbox "-156 18.8 -154.7 20.3" --out_dir /path/to/output
#
# shellcheck disable=SC2086
"${CONDA_EXE:-conda}" run --live-stream --name dem \
    python -m scalene --no-browser --json --outfile "${outdir}/profile.json" --- \
    "${basedir}/get_dem.py" -o "${outdir}" --bbox ${bbox} ${compute}
