# G-real output equivalence test

## Hourly full-field fallback

Two isolated 7,800 s runs used the same deployed dense-face ELF and differed only in `Problem.Name` and `Benchmark.VtkEvery` (1 versus 6). They ran on separate HPCC physical cores. Both reached 7,800 s and passed the same water/salt/energy and mineral checks.

The following files had identical SHA256 values between runs: `final_state.txt`, `budget.csv`, `film_budget.csv`, `thermal_budget.csv`, `mineral_budget.csv`, `material_budgets.csv`, `native_fluxes.csv` and `depth_profiles_compact.csv`. Full output wrote 14 VTU files and 247 MiB; hourly fallback wrote 4 VTU files and 90 MiB for this short window. Thus the fallback changed storage only, not the accepted numerical trajectory.

## Sparse detailed film faces

The production candidate samples detailed top-film faces every 3,600 s while retaining accepted-step integrated film history. Its formal Slurm 7,800 s run passed. `final_state.txt`, `budget.csv`, `film_budget.csv`, `thermal_budget.csv`, `mineral_budget.csv`, `material_budgets.csv`, `native_fluxes.csv`, and `depth_profiles_compact.csv` were SHA-256 identical to the dense-face reference.

`film_faces.csv` decreased from 10,424,694 to 608,431 bytes (94.16%). Both cases retained four VTK checkpoints under the hourly fallback. This demonstrates output-frequency equivalence for the tested 7,800 s window; it is not evidence of time-step, grid, or full-window convergence.
