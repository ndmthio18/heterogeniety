# Method and acceptance order

1. Freeze `20261103_v13_bottom_boundary_campaign/track3d_r02/source_filter` and merge only the v17 compact-profile diagnostic header.
2. Generate a 4 mm port-fraction map on the unchanged 768-face lower boundary using exact line/circle-sector integration.
3. Build an isolated nonisothermal executable on Frodo. Replace host-native ISA with the common `x86-64-v3` target for AMD-to-Intel portability; do not alter physics or tolerances.
4. Relocate only absolute dynamic-library names for HPCC. Preserve pre- and post-link ELF hashes.
5. Run gates A-F in order. Failed launch attempts remain provenance and are not numerical failures.
6. Use one MPI process. Benchmark 1/2/4/8 computational threads with BLAS/OpenMP nesting disabled and identical endpoint states.
7. Use hourly full fields (`CheckpointOutputInterval=600`, `VtkEvery=6`) unless selective event output is independently verified. Compact accepted-step budgets and 1 mm profiles remain high-frequency.
8. Launch the two cases in separate directories only after capacity and multicore admission. Verify 174 h evaporation, conservation and archive hashes before comparison.

Numerical equivalence requires identical phase states and maximum component-wise normalized primary-field difference below `1e-7`. Water, salt and energy relative residuals must each remain below the input limit `1e-6`.
