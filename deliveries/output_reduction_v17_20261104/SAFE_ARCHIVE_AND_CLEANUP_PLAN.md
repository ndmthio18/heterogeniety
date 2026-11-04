# Safe archive and cleanup plan

This is a proposal only. No listed campaign file has been deleted.

## Retention classes

1. **Authoritative full-resolution archive:** retain the current hash-verified local incremental archive set until a consolidated replacement has been copied to independent storage and every member hash has been reverified.
2. **Working scientific set:** retain the v17 sparse fields at 0, 24, 60, 84, 96, 108, 120, 144 and 174 h, their consistent PVD files, manifests, compact budgets, native flux summaries and derived figures.
3. **Reproducibility core:** always retain source, exact inputs, build and binary hashes, mesh, forcing data, effective parameters, logs, run status, numerical acceptance, scalar histories and transfer receipts.
4. **Failure evidence:** retain sal failures, failed grid gates, repair logs and superseded launch records. Their small-to-moderate footprint is scientifically material.
5. **Ephemeral transport material:** remove only after destination archive and member hashes pass and a receipt is written.

## Explicit proposed deletion list

Nothing below should be removed until the user approves a destructive cleanup and a fresh pre-delete check reproduces the stated coverage.

| Proposed target | Preconditions | Expected recovery |
|---|---|---:|
| Frodo `track2d/raw/runs/{B0,B1,B2,B3}/*.vtu.gz` | 4,228 local archive entries and sparse PVDs reverified | 2.406 GiB |
| Frodo `track2d_g_conditional_r02/raw/runs/{G1,G2,G3}/*.vtu.gz` | 3,171 local archive entries and conditional status labels retained | 2.061 GiB |
| Frodo `track3d_r02/raw/runs/{B0,B1,B2,B3,G1,G2}/*.vtu.gz` | 6,342 local archive entries, completed status and downstream results reverified | 33.856 GiB |
| One of Frodo `plot_snapshot_20261104_1120/` or `plot_snapshot_20261104_1120.tar` | preserve the other and its member manifest | 0.205 GiB |
| One of local `plot_snapshot_20261104_1120.tar` or `track3d_current_snapshot_20261104/` | already verified: 78 files, 220,521,389 bytes, zero SHA mismatches | 0.205 GiB |

Maximum first-stage recovery is therefore about 38.528 GiB on Frodo and 0.205 GiB locally.

## Explicit exclusions

- Do not touch active 3D G3, its live PVD, its latest uncompressed fields, supervisor, logs or incremental-backup index.
- Do not delete any of the 24 local verified incremental archives individually.
- Do not delete the only copy of a failed attempt, refined-grid failure, repair source, accepted scalar history, native replay output, figure source, or manifest.
- Do not delete sal historical evidence merely because newer Frodo runs exist.
- Do not delete v13 accepted inputs or binaries.

## Approved-cleanup procedure

1. Freeze a fresh status snapshot; require no target case to be active.
2. Recount expected frames and compare every target path to `verified_index.json` SHA256.
3. Re-run sparse PVD/VTK validation and confirm downstream results exist.
4. Write a machine-readable deletion manifest containing exact paths, sizes and hashes.
5. Delete only manifest-listed files; never use a broad campaign-root pattern.
6. Recount remaining files, check active processes, and record actual recovered bytes.
7. Keep the deletion receipt with `PROGRESS.md` and the full archive index.

## Future archive policy

- Back up by content hash and copy only absent/changed files. `incremental_backup.py` implements this for directory targets.
- A transport tar is a temporary envelope, not a new archival generation. Remove it only after transfer SHA and member SHA verification.
- Require one complete independent full-resolution archive plus one sparse working set; do not keep repeated cumulative full tars on the same disk.
- Consolidate old incremental series only on a destination with enough admission margin to hold both old and new copies during verification.
