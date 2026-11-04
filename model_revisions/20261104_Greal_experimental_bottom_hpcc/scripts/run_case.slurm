#!/bin/bash
set -euo pipefail
: "${GREAL_ROOT:?}" "${GREAL_WORKDIR:?}" "${GREAL_INPUT:?}"
cd "$GREAL_WORKDIR"
export DUMUX_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/rmprog/slurm/v22.05.7/bin
"$S/srun" --ntasks=1 --cpus-per-task="${SLURM_CPUS_PER_TASK:-1}" --cpu-bind=cores \
  /usr/bin/time -v "$GREAL_ROOT/solver_wrapper.sh" "$GREAL_INPUT" \
  > simulation.log 2>&1
