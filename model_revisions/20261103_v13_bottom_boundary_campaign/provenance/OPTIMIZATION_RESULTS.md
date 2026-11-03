# 3D performance optimization results — 2026-11-02

Final benchmark stage: completed. Production v12/v13 unmodified. Selected family: `build_cached_ni`, threads: 4, options: `{'Newton.EnablePartialReassembly': 'true', 'Benchmark.AmgILU': 'true'}`.

Original-grid short-segment measured speedup versus same-host one-thread baseline: 3.028x (455.27 → 150.36 s). This is a 7800–9600 s segment; not qualification for full 174 h production.

| Case | Threads | Step wall s | AMG setup s | Krylov s | Linear iterations | Max normalized field difference | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| s1_continuous | 1 | 1652.86 | 16.41 | 495.50 | 2409 |  | completed |
| s1_t1_a | 1 | 456.47 | 4.18 | 160.93 | 1001 | 1.6468813950318825e-12 | completed |
| s1_t2_a | 2 | 339.29 | 4.20 | 164.71 | 1001 | 1.6468813950318825e-12 | completed |
| s1_t2_b | 2 | 333.86 | 4.18 | 161.66 | 1001 | 1.6468813950318825e-12 | completed |
| s1_t1_b | 1 | 454.06 | 4.16 | 160.36 | 1001 | 1.6468813950318825e-12 | completed |
| s1_t4_a | 4 | 284.40 | 4.19 | 161.06 | 1001 | 1.6468813950318825e-12 | completed |
| s1_t4_b | 4 | 287.89 | 4.23 | 162.70 | 1001 | 1.6468813950318825e-12 | completed |
| s1_cached_t1 | 1 | 400.03 | 4.21 | 162.78 | 1001 | 0.0 | completed |
| s1_cached_t2 | 2 | 297.04 | 4.18 | 161.63 | 1001 | 0.0 | completed |
| s1_cached_t4 | 4 | 249.93 | 4.23 | 160.61 | 1001 | 0.0 | completed |
| s1_cached_selected_repeat | 4 | 259.35 | 4.36 | 166.80 | 1001 | 0.0 | completed |
| s2_partial | 4 | 250.42 | 4.77 | 182.98 | 1013 | 2.0074248245955898e-12 | completed |
| s2_ilu | 4 | 187.68 | 6.83 | 89.23 | 685 | 1.6445312038668843e-12 | completed |
| s2_combined | 4 | 149.41 | 6.50 | 84.99 | 699 | 1.0449311496904278e-12 | completed |
| s2_selected_repeat | 4 | 150.36 | 6.53 | 85.45 | 699 | 1.0449311496904278e-12 | completed |
| s3_dt150 | 4 | 222.99 | 9.79 | 122.11 | 999 |  | completed |
| s3_dt600 | 4 | 93.40 | 3.91 | 54.60 | 449 |  | completed |
| s4_vtk_stride3 | 4 | 147.27 | 6.51 | 84.77 | 699 | 0.0 | completed |

## Temporal screen

These comparisons use the same selected implementation and different step caps. Budget closure alone is not temporal accuracy. The 300 s production cap is retained.

| Metric at 9600 s | dt150 | dt300 | dt600 | dt600 minus dt150 |
|---|---:|---:|---:|---:|
| water_mol | 1.61883342 | 1.61883063 | 1.61882546 | -7.9684e-06 |
| salt_total_mol | 0.0300178594 | 0.0300177416 | 0.0300175214 | -3.38025e-07 |
| coarse_salt_mol | 0.0157919338 | 0.0157918315 | 0.0157916362 | -2.9754e-07 |
| fine_salt_mol | 0.0142259256 | 0.0142259101 | 0.0142258852 | -4.04846e-08 |
| C_max_mol_L | 1.22666456 | 1.22549648 | 1.22326848 | -0.00339608 |
| S_min | 0.996358168 | 0.996401664 | 0.996490432 | 0.000132264 |
| cumulative_interface_adv_mol | 7.57097524e-05 | 7.57235434e-05 | 7.57555523e-05 | 4.57999e-08 |
| cumulative_interface_diff_mol | -5.15956424e-07 | -5.36448008e-07 | -5.77190233e-07 | -6.12338e-08 |
| T_min_K | 291.426764 | 291.438145 | 291.459696 | 0.032932 |
| T_max_K | 292.837311 | 292.843839 | 292.855601 | 0.0182901 |

## Acceptance and limits

- Thread and solver variants require identical phase states and component-wise normalized maximum primary-field difference <1e-7; all selected candidates retain original Newton/linear tolerances.
- Water/salt/energy relative budget threshold remains 1e-6; mineral complementarity and finite-state checks are retained.
- Precipitation, dissolution and retained-solid tests on the small existing reaction mesh are functional tests, not original-grid scaling tests.
- The saved full primary-variable/phase snapshot is a segment benchmark input. Accounting resets at segment start; this is not a production restart feature.
- No independent claim about long-time precipitation onset, high-solid-state robustness, mesh convergence or experimental validation follows from this performance benchmark.
- MPI remains disabled until reductions, partition ownership, seeding, IDs and output are implemented and independently verified. GPU migration is not justified by this CPU screen.
- The tested VTK stride preserves checkpoint times and every-step balances. Default production output is retained absent a substantial measured benefit.
- Hardware comparison: Frodo was measured against liqin only in an initial 600 s segment, under different concurrent loads. See host_probe_comparison.json; do not extrapolate that factor to full production.

## Reproduction

Use the immutable build manifests, per-case `case.input`, `manifest.json`, `initial_state.txt`, source patches, full primary-variable outputs and recorded commands. Do not mix binary families when interpreting a comparison. Source and dependencies are isolated under `/temp/zhixin/heterogeneity_performance_v14_20261102` on Frodo.

## Physical-field temporal comparison

See TIMESTEP_ASSESSMENT_ZH.md and timestep_physical_comparison.json. Phase-switch primary-variable errors in stage3.json must not be interpreted as saturation errors. At 600 s versus 150 s, maximum concentration difference is 0.003566 mol/L, temperature difference 0.03382 K and liquid saturation difference 0.0004173; six cells differ in phase classification. The finer run is not a converged reference.
