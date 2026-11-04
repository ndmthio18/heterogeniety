#!/bin/bash
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=48:00:00
set -eu
cd /tmp/zhixin_sal_film_v16_20261103
export DUMUX_NUM_THREADS=4 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export TMPDIR=/tmp/zhixin_sal_film_v16_20261103/tmp
mkdir -p "$TMPDIR"
srun --cpu-bind=cores venv/bin/python campaign.py "$@"
