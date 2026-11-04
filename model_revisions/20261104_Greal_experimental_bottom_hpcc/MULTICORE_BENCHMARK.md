# HPCC multicore benchmark

## Design

The formal benchmark uses the admitted Slurm `cnmix` partition, one MPI task,
and 1, 2, 4, or 8 scheduler-bound CPU cores.  Each case restarts from the same
accepted 7,800 s G-real state and advances to 9,600 s with unchanged 300 s
maximum step, nonlinear tolerances, mesh, physics, and output policy.  The four
cases are chained by `afterok` dependencies to avoid node-load confounding.

The selected core count is the lowest measured Slurm elapsed time among cases
whose material state is equivalent to the one-thread result at a maximum
component-relative tolerance of `1e-7`.  Scheduler allocation alone is not
treated as evidence of acceleration; `Elapsed`, `TotalCPU`, `MaxRSS`, solver
step timings, and state differences are retained.

## Results

| Threads | Slurm job | Node | Elapsed (s) | Speedup | Efficiency | Observed CPU | Peak RSS (kB) | State difference |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | 16293333 | ibc11b11n01 | 380 | 1.000 | 1.000 | 91% | 340136 | 0 |
| 2 | 16293334 | ibc11b11n01 | 297 | 1.279 | 0.640 | 123% | 340576 | 0 |
| 4 | 16293335 | ibc11b11n01 | 259 | 1.467 | 0.367 | 140% | 350412 | 0 |
| 8 | 16293336 | ibc11b11n23 | 174 | 2.184 | 0.273 | 176% | 352596 | 0 |

All four endpoint states were exactly equal in the parsed state table.  Eight
threads gave the shortest elapsed time and were selected for the two 48 h-limit
production jobs.  This is a wall-time decision, not a claim of efficient
eight-core scaling: measured CPU utilization was only 176%, and the eight-core
case ran on a different node of the same cluster.  The node change remains a
benchmark limitation.
