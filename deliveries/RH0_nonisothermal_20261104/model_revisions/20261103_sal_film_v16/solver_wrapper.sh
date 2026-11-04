#!/bin/bash
export LD_LIBRARY_PATH="/tmp/zhixin_sal_film_v16_20261103/runtime/lib"
export OMPI_MCA_mca_base_component_path="/tmp/zhixin_sal_film_v16_20261103/runtime/plugins"
export OPAL_PREFIX="/tmp/zhixin_sal_film_v16_20261103/runtime"
for key in ${!SLURM_@} ${!PMI_@} ${!PMIX_@} ${!OMPI_COMM_WORLD_@}; do
 case "$key" in SLURM_*|PMI_*|PMIX_*|OMPI_COMM_WORLD_*) unset "$key" ;; esac
done
export PATH="/tmp/zhixin_sal_film_v16_20261103/runtime/bin:$PATH"
exec "/tmp/zhixin_sal_film_v16_20261103/build_ni1/solver_elf" "$@"
