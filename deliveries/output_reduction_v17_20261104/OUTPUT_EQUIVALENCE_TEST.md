# Original versus reduced-output equivalence test

## Design

Two isolated 3D original-grid runs used the same frozen ELF SHA256 `9b1422e33fb76423322b081e414206e22777548fca0b703d6e285186a4fe63e5`. Inputs differed only in `Problem.Name` and `Benchmark.VtkEvery` (1 versus 6). Physics, mesh, initial state, 600 s checkpoint grid, time-step limits, Newton/linear settings, tolerances and 7,800 s end time were identical. Both ran concurrently on otherwise unused Frodo CPUs 6 and 7, one thread each, without touching active G3 on CPU 5.

Both runs completed with exit status 0 at 7,800 s (0.1666667 h evaporation) and accepted 46 steps.

## Numerical equivalence

| Check | Result |
|---|---|
| Full final state, 24 exported cell arrays, 30,720 cells | maximum absolute difference 0 |
| `budget.csv`, 47 rows | maximum absolute and relative difference 0 |
| `film_budget.csv`, 47 rows | maximum absolute and relative difference 0 |
| `thermal_budget.csv`, 47 rows | maximum absolute and relative difference 0 |
| `mineral_budget.csv`, 47 rows | maximum absolute and relative difference 0 |
| F36 final 40-bin concentration profile | maximum difference 0 M |
| W3 final 40-bin concentration profile | maximum difference 0 M |
| Integrated bottom/interface flux columns | identical through identical accepted-step budget histories |

This is exact numerical equality for the tested short window, not a new grid/time-step convergence study and not physical validation of the boundary model.

## Output and performance

| Metric | Original | Reduced | Change |
|---|---:|---:|---:|
| VTU frames | 14 | 4 | −71.4% |
| VTU + PVD bytes | 194,565,064 | 56,169,423 | −71.13% |
| Total downloaded run bytes | 221,307,367 | 82,910,939 | −62.54% |
| Sum of measured output time | 11.8483 s | 2.70065 s | −77.21% |
| Wall time | 473.37 s | 462.22 s | −2.36% |

Newton and linear-solver timing varied slightly under concurrent system load, but accepted state histories were byte-for-value identical. Output reduction did not add wall overhead in this test.

## PVD/reader validation

Both regression PVD files and all 18 referenced VTUs loaded with local VTK 9.3.1; all datasets had nonzero points, cells and cell arrays. Separately, all 13 sparse PVDs and 117 VTUs loaded on Frodo with VTK 9.5.2 and locally with VTK 9.3.1.

Frodo's packaged `pvpython 5.11.2` segfaulted during ParaView proxy creation, including after removing explicit proxy deletion; sal's `pvpython 6.0.0` lacked its `paraview` Python module. These are host ParaView installation failures, not field-reader failures. Therefore the evidence supports PVD consistency and the same VTK XML reader used underneath ParaView, but does not falsely claim a successful GUI/proxy test on those broken installations. A workstation ParaView GUI smoke test remains a deployment check before users discard a full archive.

Machine-readable evidence is in `regression/equivalence_results.json`, `regression/pvd_vtk_validation.json`, `vtk_reader_validation.json` and `vtk_reader_validation_local.json`.

## Diagnostic-only compact-profile overlay

A third isolated run used the separately built diagnostic overlay while retaining the reduced-output run's physics, mesh, initial state, checkpoint grid, `VtkEvery=6`, tolerances and 7,800 s endpoint. It completed with exit status 0 and the same 46 accepted steps (47 records including the initial state).

| Check against reduced-output reference | Result |
|---|---|
| Full final state, 24 arrays × 30,720 cells | maximum absolute difference 0 |
| Four core budget tables, 47 rows each | maximum absolute and relative difference 0 |
| Final compact F36/W3 profile, 80 bins, compared with full VTK | maximum concentration difference `9.55e-15` M |
| Final compact liquid-volume bins | maximum difference `4.72e-20` m3 |
| Compact rows | 3,840: 47 unique simulation times × 80 bins, plus one explicit 80-bin repeat at the 7,200 s pre-equilibration/evaporation phase boundary |

The machine-readable acceptance is `regression/profile_overlay_equivalence.json` (`state: passed`). This proves the new writer was non-perturbing for the tested short run; it is not evidence of long-window convergence or physical validation.
