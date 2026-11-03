# sal resource plan

Initial live inventory: AMD3990X,64 physical/128 SMT CPUs,251GiB RAM (~180GiB available), /tmp tmpfs ~120GiB free. Slurm debug, no oversubscription; several unrelated active/pending jobs and existing7.5/8mm cases remain untouched. Initial unrelated allocation122 logical CPUs leaves6; floor(70%*6)=4 allocated logical CPUs permits two independent single-thread cases (Slurm allocates both SMT siblings per physical core).

B short and production arrays are throttled%2; each task requests1 CPU and sets DUMUX_NUM_THREADS=1, OMP/BLAS=1, nice10. No mpirun. B long cases have48h wall cap and4GiB scratch reserve; each begins from initial conditions. Source, output directories, PIDs, logs and inputs are independent. /usr/bin/time records CPU/RSS. The configured Slurm RealMemory=1MB is erroneous; do not override site allocation policy with unschedulable RAM requests. Physical free memory and per-process RSS remain monitored.

G jobs are submitted held. resource_dispatch.py rechecks unrelated allocations before releasing this campaign's held jobs, reserves B peak4 logical CPUs while B remains queued/running, caps this campaign at8 logical CPUs and70% of capacity not allocated to unrelated work. Geometry development/build on the idle Frodo workstation does not delay B. All new regression/prediction cases run on sal; Frodo is used only for a one-core nice15 build with pinned dependencies. Lack of an admissible sal slot is a resource wait, not a solver failure.

Raw VTUs are reversibly gzip-compressed with raw and compressed SHA256 records. backup_incremental.py downloads closed fields and metadata, verifies transport and per-member hashes, and removes only its verified disposable transport tar. Original raw gzip fields and all failed attempts remain. No old revision or unrelated data cleanup is authorized. /tmp is volatile, so final completion requires all final fields and metadata verified locally.

Monitor every two hours. No parameter/tolerance/time-step changes or restarts merely for slowness. Failed physical/numerical gates block downstream production. A repaired test reference or launcher must retain original evidence and document the precise change.

## Two-host extension after explicit user steering

Frodo verified12physical/24logical cores,~22GiB available RAM,237GiB scratch and nearly idle; no Slurm/PBS.2D now uses bounded local supervisor, max6single-thread processes on physical CPUs4–9 (50% of physical capacity),nice10,48h/case,8GiB free-memory and20GiB scratch admission guard. No heavy login-node job: Frodo is the user's authorized compute workstation with existing simulation/build environment. cxhpc verified through liqin bridge,32physical/64logical cores,load~15,~219GiB available memory and495GiB storage; not used because Frodo already compatible/idle. No host-key bypass. sal2D jobs19195–19200 were all held/pending and cancelled;3D arrays restored concurrency2. Source/metadata and cancellation receipts retained.


## Active repair supersedes historical placement — 2026-11-03 16:49 UTC

The user requested diagnosis and repair of3D. Active3D is isolated Frodo track3d_r02, CPUs4–9 max6serial tasks,1thread,nice10,6hshort/48hproduction,8GiB RAM/30GiB scratch admission. Launch available22.15GiB RAM/226.21GiB scratch. The2D supervisor is terminal; no competing2D children remain. Any2DG repair must coordinate this shared pool. Unrelated CPU0 simulation untouched. Old sal B2/B3 finish independently; never-started pending long/G duplicates cancelled and preserved. See track3d_r02/METHOD.md.
