#!/bin/bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
module purge
module load compilers/gcc/v12.2.0
module load mpi/openmpi-gcc12/v4.1.4
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
# The solver is deliberately serial MPI; keep the Slurm cgroup but remove rank
# variables before OpenMPI singleton initialization.
for key in ${!SLURM_@} ${!PMI_@} ${!PMIX_@} ${!OMPI_COMM_WORLD_@}; do
  case "$key" in SLURM_*|PMI_*|PMIX_*|OMPI_COMM_WORLD_*) unset "$key";; esac
done
exec "$ROOT/build/solver_2d" "$@"
