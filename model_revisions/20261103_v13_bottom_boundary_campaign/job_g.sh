#!/bin/bash
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=48:00:00
set -eu
cd /tmp/zhixin_v13_bottom_boundary_20261103
export DUMUX_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export TMPDIR="$PWD/tmp"
mkdir -p "$TMPDIR"
srun --cpu-bind=cores venv/bin/python campaign_g.py "$@"
