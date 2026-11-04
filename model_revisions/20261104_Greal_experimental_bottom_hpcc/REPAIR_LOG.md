# Deployment and numerical repair log

1. The first Frodo ELF used `-march=native` on AMD. It was rejected before HPCC execution and rebuilt with the common `x86-64-v3` ISA. Physics and solver settings were unchanged.
2. HPCC boundary attempt 01 exited before MPI/model initialization because Windows tar transport lost the executable bit on the bundled loader. Execute permission was restored; the failure log is retained.
3. Attempt 02 exited before MPI/model initialization because two DuMuX dependencies had Frodo absolute NEEDED paths. `patchelf 0.18.0` changed only those NEEDED entries to their basenames; original and deployed ELF hashes are retained.
4. Attempt 03 reached MPI singleton initialization but lacked `orted`. The exact previously recorded Frodo OpenMPI `orted` was relocated to this campaign's bundled loader/library path and hash-pinned.
5. Attempt 04 passed all hydrostatic, donor-component and enthalpy assertions. No tolerances, physics, grid or fit parameters were changed by repairs 1--4.
6. The login shell did not expose Slurm commands, leading initial discovery to classify HPCC as standalone. A deeper role audit found `slurmd` and `/rmprog/slurm/v22.05.7/bin`. Two active direct-SSH gate diagnostics were terminated, preserved and excluded from formal scheduler acceptance. All subsequent gates and production use Slurm cgroups/affinity.
