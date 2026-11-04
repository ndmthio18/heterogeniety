Attempt19163 failed before solving in MPI_Init because the frozen OpenMPI runtime detected Slurm PMI. This is a single-process threaded solver; force ess=singleton and pmix=isolated within the unchanged Slurm CPU allocation. No physical/numerical changes. Original wrapper, manifest, gate log and raw preserved in provenance/launch_attempt01.
Attempt19164 forced isolated PMIx but job size was unavailable. Preserve attempt02; remove singleton overrides and strip Slurm/PMI rank-discovery environment only inside the one-process solver wrapper. Slurm still schedules, tracks and binds parent and child; no allocation bypass. Controller retains Slurm job IDs.

Attempt03 exposed host env executable loading bundled glibc. Replaced env subprocess with bash-only parameter expansion; no solver setting changes.

Attempt04 reached singleton initialization but lacked orted. Added exact Frodo orted with relocated loader, libraries unchanged; recorded hashes.
