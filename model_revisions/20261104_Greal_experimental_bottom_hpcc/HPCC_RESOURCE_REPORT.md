# HPCC resource and admission report

Initial discovery on 2026-11-04 was misleading because Slurm clients were absent from the login shell `PATH`. A role audit found `slurmd` and the client installation at `/rmprog/slurm/v22.05.7/bin`; the real node is `ibc12b01n05` in cluster `tansuo1000`, controlled by `ibrmserver01`. All admitted gates and production therefore use real Slurm allocations. Two partially run direct-SSH diagnostic cases were terminated and retained when this was discovered; they are not accepted scheduler evidence.

- Observed node CPU: 56 physical cores, 2 x Intel Xeon Gold 6258R, one hardware thread per core.
- Memory: about 187 GiB total.
- Persistent work: Lustre `/WORK`, about 7.0 PiB total and 4.9 PiB free at admission; inode use 5%.
- RAM filesystem: `/ram`, about 57 GiB free at admission.
- Slurm: `select/cons_tres`, `CR_CORE`, `task/affinity,task/cgroup`, `proctrack/cgroup`.
- Gate partition: `cntest` (four 28-core nodes idle at audit). Production candidate: `cnmix` or `cnall`, subject to allocation and benchmark.
- Existing user jobs were present and unrelated; they are not modified.
- Remote campaign root: `/WORK/hulm_work/zhixin/Greal_experimental_bottom_hpcc_20261104`.
- Execution control: `sbatch`/`srun`, one Slurm task and measured computational threads per case; no multi-rank model execution.

Frodo is AMD Ryzen while HPCC is Intel. The first build used `-march=native` and was rejected for deployment. The frozen portable build uses `-march=x86-64-v3`, supported by both hosts. Dynamic runtime migration is hash-pinned. Deployment launch repairs changed Unix execute bits, absolute ELF dependency names and the singleton `orted` path only; no physical or numerical input changed.

The site reports `RealMemory=1` in partition metadata despite observed 187 GiB node RAM, so explicit memory requests require administrator clarification; gate RSS is recorded independently.

Formal `cnmix` short cases used about 274 MiB (six layers) and 381 MiB (twelve layers). The measured hourly-output projection is 6.488 GiB for both production cases including a conservative 750 MiB compact-history allowance per case; the admission check retained a 30 GiB reserve and passed. Formal one-task scaling selected eight threads by wall time (174 s versus 380 s for one thread), although observed utilization was only 176% and parallel efficiency 27.3%. Greal-75 job `16293418` and Greal-81 job `16293419` were observed actually running under Slurm on `cnmix`; submission alone was not treated as launch evidence.
