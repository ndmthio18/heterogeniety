# Disk-usage audit for the v13 2D/3D campaign

Audit time: 2026-11-04 13:03–14:20 UTC. This was a read-only audit of the scientific campaign. No original simulation output, archive, failure record, or active file was deleted. The separate v17 regression and sparse-working-set implementation is recorded below and did not alter any v13 input or executable.

## Host-level capacity

| Location | Filesystem state | Campaign footprint | Main consumers |
|---|---:|---:|---|
| Frodo `/temp` | 3.6 TiB total, 3.1 TiB used, 372 GiB available (90% used) | 52 GiB | `track3d_r02` 45 GiB; `track2d` 3.5 GiB; conditional 2D G 2.8 GiB; extracted and tarred plot snapshot 211 MiB each |
| sal `/tmp` | 126 GiB total, 77 GiB used, 50 GiB available (61% used) | 949 MiB | historical/superseded `raw` 611 MiB; venv 163 MiB; runtime 68 MiB; track2d 24 MiB; builds about 41 MiB |
| Local D: at audit | 1024 GiB total, 971.3 GiB used, 52.7 GiB available | 61.037 GiB in the campaign directory | 28 tar files 60.482 GiB; VTU.GZ 0.200 GiB; CSV 0.130 GiB |

The implementation created a separate 0.904 GiB local sparse working set plus isolated equivalence records; after the final profile-overlay gate the complete v17 evidence tree was 1.264 GiB and D: had 51.435 GiB free. They are not counted as pre-existing campaign use.

## Field and archive inventory

Frodo contains 15,087 compressed VTU files (42.017 GiB), two currently uncompressed VTUs (0.0328 GiB), 81 PVD files (0.0011 GiB), and one 0.205 GiB plot transport tar. The two raw VTUs belong to current activity and are not cleanup candidates. sal contains 233 VTU.GZ files (0.382 GiB) and 16 PVD files from superseded/failed attempts; these remain provenance evidence.

Local storage contains 24 tar archives with transfer receipts and verified archive hashes, totalling 60.235 GiB. Four additional tars total 0.246 GiB: a plot snapshot, a light 2D delivery, and two negligible partial previews. The large archive series is incremental: member counts and the union hash index show new/changed files rather than repeated full snapshots. It is one logical full-resolution archive set, not 24 independently disposable full copies.

## Case completion, acceptance, backup, and postprocessing

| Cases | Numerical state | Full local compressed-field coverage | Downstream state | Sparse working set |
|---|---|---:|---|---|
| 2D B0–B3 | completed, 174 h, accepted | 4,228/4,228 VTU.GZ plus PVD/status; raw and gzip SHA recorded | all four `verification.json` passed at 174 h | 9 frames/case, prepared |
| 2D G1–G3 | completed, 174 h, numerically accepted but scientifically conditional | 3,171/3,171 VTU.GZ plus PVD/status | all three verification files passed at 174 h | 9 frames/case, prepared |
| 3D B0–B3 | completed, 174 h, accepted | 4,228/4,228 VTU.GZ plus PVD/status | full native replay repaired and accepted; result summaries complete | 9 frames/case, prepared |
| 3D G1–G2 | completed, 174 h, accepted as exploratory cases | 2,114/2,114 VTU.GZ plus PVD/status | profiles, budgets and accepted-step native throughput integrations complete | 9 frames/case, prepared |
| 3D G3 | active; 65.42 h at the formal status snapshot and later advancing | last backup index 349 fields; 418 fields existed at the storage scan | not terminal; no final postprocessing claim | deliberately excluded |

“Accepted” above means the registered numerical completion/budget gate passed. It does not convert the conditional 2D G grid study or exploratory boundary mechanisms into physical validation.

## Duplicate physical copies

- Completed raw fields exist on Frodo and as an independently verified local incremental archive set. This is intentional two-copy protection and becomes a cleanup opportunity only after explicit approval.
- The Frodo plot snapshot exists both as an extracted 211 MiB directory and a 211 MiB tar.
- Locally, `plot_snapshot_20261104_1120.tar` and `track3d_current_snapshot_20261104` contain the same 78 files. All 220,521,389 member bytes were compared by size and SHA256 with zero mismatches. One copy can later be removed, recovering 0.205 GiB.
- The 24 verified local incremental archives must not be individually pruned: together they provide the complete independent full-resolution archive. Consolidation to another verified storage target must precede replacement.
- sal's runtime, venv and builds overlap conceptually with newer deployments, but the sal tree is retained as failed/superseded execution provenance. It is not an immediate deletion target.

## Recoverable storage, subject to explicit cleanup approval

Completed VTU.GZ fields on Frodo occupy 38.323 GiB: 2D B 2.406 GiB, conditional 2D G 2.061 GiB, and completed 3D B/G1/G2 33.856 GiB. These have complete local hash-index coverage and a 9-frame/case sparse working copy. Removing only those completed remote field files after a final pre-delete audit would recover 38.323 GiB without touching scalar histories, flux histories, inputs, status, failure evidence, postprocessing, or active G3.

One of each verified plot snapshot pair can recover another 0.205 GiB on Frodo and 0.205 GiB locally. No other local deletion is currently classified as safe without first creating and verifying a consolidated archive on independent storage.

Evidence: `status_tracks.py` live output, the three `verified_index.json` files, `B2D_final_backup_verification.json`, archive transfer receipts, per-case status/results, and the v17 sparse manifests.
