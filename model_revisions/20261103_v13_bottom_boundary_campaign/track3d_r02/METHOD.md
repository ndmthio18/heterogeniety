# 3D launcher repair r02 — 2026-11-03

## Diagnosis

The original B controller inherited SHORT_WALL_S=3600 from its runner. On sal, the original-grid baseline (2 h pre-equilibration + 10 min evaporation) consumed 26 min 37.21 s (99% CPU, 303.5 MiB peak RSS). B0/B1 short cases were terminated by that one-hour wall guard after 1.583333 h evaporation. This was a launcher wall-budget mismatch, not a Newton convergence failure. The all-short dependency barrier consequently prevented the 174 h B jobs from starting. G already configured a six-hour short limit.

## Repair and authorization

Following the user's request to diagnose and repair, and their prior authorization to use Frodo/cxhpc, the isolated track3d_r02 uses an explicit six-hour wall cap per short solve. Production retains the original 48-hour cap. There is no change to physical parameters, source equations, mesh, numerical tolerance, timestep, retry limit or fitting freedom. No unverified VTU restart is used; new cases start from the original initial conditions.

Frodo is the authorized compute workstation. A local dependency supervisor replaces Slurm launch metadata, explicitly allows only hostname frodo, uses an exclusive lock, and does not impersonate a scheduler. At most six serial processes run on physical CPUs 4–9, one thread each, nice 10. Admission requires 8 GiB available RAM and 30 GiB free scratch; each solver retains its 4 GiB reserve. At launch 22.15 GiB RAM and 226.21 GiB scratch were available. The unrelated Paper 2 process on CPU 0 was left untouched. Any later 2D G repair must share this resource budget rather than launch a second independent six-core pool.

Original source/input hashes were checked against compiled manifests. The unchanged native Frodo ELFs and their dependencies passed SHA256 and loader checks:

- B solver: 9b1422e33fb76423322b081e414206e22777548fca0b703d6e285186a4fe63e5
- G solver: f0205489a215670ac56650c5535f3544f8a4d1ef9365e2c630b6e973129f4868
- Native replay: d2c509627d01926c922f39c6a0096014d2f8809f32fa8aab7cc3be5fb54aea82

Original sal failed/running attempts remain preserved. Only verified never-started pending production/G jobs 19183,19187–19190 were cancelled to avoid duplicate launches; receipts are in provenance. Running old B2/B3 were not interrupted. The prior cancelled sal 2D jobs 19195–19200 remain cancelled.

## Acceptance sequence and current evidence

Actual launch: 2026-11-03 16:46:44 UTC, Frodo supervisor PID 2824177, baseline controller PID 2824190. Read fresh status rather than assuming these PIDs remain current.

The B baseline repeats six reaction gates, injected rollback and the original-grid regression. Each B short runs only after this baseline passes; all four shorts must pass before B174h. G boundary probes and baseline precede G dynamic gates; those precede G174h. Independent failures block their dependents, with no automatic retries.

At 16:49 UTC the G boundary probes passed for all four configurations (maximum donor relative error 2.97e-16; heat relative error 3.00e-15). The baseline regression was still running; no new 174 h production had started. Initial r02 backup verified 311 files. The sal historical backup index covered 658 paths. This establishes deployment and probe acceptance, not completion of the short-run repair validation, full-window numerical convergence or physical validation.

## Evidence and operation

Read DEPLOYMENT.json, provenance/stage_receipt.json, provenance/live_verification.json, provenance/launcher_repair.patch and provenance/sal_pending_superseded.json. Source and initial-controller versions are retained locally. Use parent status_tracks.py, backup_frodo_3d.py and MONITOR_INSTRUCTIONS.md. Remote root is /temp/zhixin/v13_bottom_boundary_campaign_20261103/track3d_r02 via SSH iws_zhixin; archived attempt01 remains /tmp/zhixin_v13_bottom_boundary_20261103 on sal.

The repository delivery excludes raw fields, executable binaries, transport archives and comparison NPZs. Reconstruct reference arrays with the parent prepare_reference.py and the previously hash-verified v13 archive; copy the resulting baseline_reference into this isolated root before a fresh deployment. No standalone, dependency-free build is claimed.


### Follow-up verification, 18:12 UTC

Baseline and all four B short gates passed. B0–B3 full174h predictions launched17:24:15UTC and reached7.25–7.4167h with live processes and maximum relative water/salt/partition residual4.41e-13. G dynamic gates remain running; G174h not launched. Both remaining historical sal shorts terminated by the same3600s wall guard. New Frodo1053-file backup verified; total1350 paths. See provenance/monitor_20261103_1811UTC.json. Full174h acceptance and comparisons remain pending.
