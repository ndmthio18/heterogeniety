# Output-reduction implementation

## Configuration

The numerical event grid remains `TimeLoop.CheckpointOutputInterval = 600` s. New tests set `Benchmark.VtkEvery = 6`, so a complete field is written hourly while accepted time steps, equations, Newton settings and maximum time step remain unchanged. The initial and final states are always written. All required checkpoints (0, 24, 60, 84, 96, 108, 120, 144 and 174 h evaporation) fall on the hourly schedule. A later two-hour option can use `VtkEvery = 12`; the same required checkpoints are all even hours and remain present.

The frozen accepted v13 executable and completed 174 h inputs were not modified. The output-only test used its SHA256 `9b1422e33fb76423322b081e414206e22777548fca0b703d6e285186a4fe63e5`. A future source overlay was built separately; its binary SHA256 is `e36ca36d532b5a42b56e27c6a50e0c3c379d5de706072a3743e91cec57166908`.

## Compact histories retained at every accepted step

The existing diagnostic path already writes:

- `budget.csv`: water/salt inventories, F36/W3 salt inventories, top and bottom rates, interface advection/diffusion, cumulative transfers and closures;
- `film_budget.csv`: evaporation, reservoir loss and gross bottom water/air/salt transfer;
- `thermal_budget.csv`: energy inventory, boundary heat and closure;
- `mineral_budget.csv`: dissolved/solid salt and complementarity;
- `material_budgets.csv`: F36, W3 and filter water/salt/energy inventories and residuals;
- `native_fluxes.csv`: gross positive/negative liquid, water, salt and heat contributions by boundary/interface kind.

The future `source_overlay/appl/campaign_diagnostics.hh` adds `depth_profiles_compact.csv` at every accepted step. It integrates each cell's vertical overlap into 1 mm F36/W3 bins and stores concentration, liquid volume, total/dissolved/solid salt. This avoids reconstructing depth profiles from high-frequency VTU files. It is a diagnostic-only write and never edits the solution vector.

## Sparse working data

`make_sparse_working_set.py` created 13 completed-case working sets, each with nine uncompressed VTUs and a new internally consistent PVD. Total local size is 0.904 GiB for 117 fields. Source compressed and working uncompressed SHA256 values are stored per frame. The authoritative full archive remains separate.

`field_series.py`, `select_available_frames.py`, `native_replay_sparse.py` and `analyze_sparse.py` resolve frames from actual PVD timesteps and read either `.vtu` or `.vtu.gz`; they never infer a 600 s filename sequence. The native replay and analysis checkpoint lists now include 108 h.

## Measured frame sizes and projections

Representative compressed means were 0.583 MiB (2D B0), 0.665 MiB (2D G1), 5.212 MiB (3D B0) and 5.971 MiB (3D G1). A 176 h total clock (2 h pre-equilibration plus 174 h evaporation) produced 1,057 fields at 600 s spacing.

| Scheme | Approximate fields/case | Frequency-only reduction | Worst observed compressed 3D fields/case |
|---|---:|---:|---:|
| Existing | 1,057 | — | about 6.16 GiB |
| Hourly, `VtkEvery=6` | 177 (capacity guard conservatively uses 178) | 83.3% | about 1.03 GiB |
| Two-hour, `VtkEvery=12` | 89 | 91.6% | about 0.52 GiB |

For six concurrent worst-size 3D cases, `capacity_guard.py` projected 7.107 GiB including 150 MiB compact-history allowance per case, leaving 363.629 GiB on the audited Frodo filesystem. The guard rejects launches below a configurable reserve and warns below a higher threshold.

## Backup behavior

`incremental_backup.py` maintains a content-hash index, copies only absent/changed files, verifies every copied file after transfer, and writes a receipt. Future remote wrappers should run the capacity guard before launch and use this content-index behavior instead of cumulative full-copy tars.

Temporary transport archives must be created under a campaign-specific directory, transferred, archive-hash checked, member-hash checked, and only then listed for cleanup. A failed or partial transfer remains explicitly marked and is never promoted to an archive.

## Compact-profile deployment gate

The future compact-profile overlay compiled separately and passed its isolated short numerical-equivalence gate. Relative to the reduced-output frozen-binary reference, all 24 final cell arrays and all 47 rows in each of `budget.csv`, `film_budget.csv`, `thermal_budget.csv` and `mineral_budget.csv` had exactly zero difference. The 80 final F36/W3 one-millimetre bins reconstructed from the full VTK agreed with `depth_profiles_compact.csv` within `9.55e-15` M in concentration and `4.72e-20` m3 in liquid volume. The overlay binary SHA256 is `e36ca36d532b5a42b56e27c6a50e0c3c379d5de706072a3743e91cec57166908`.

This makes the overlay eligible for a future campaign, but it was not substituted into active G3 or any accepted v13 run. A production launch must still record a fresh capacity result, exact source/build hash, and host-specific startup gate.
