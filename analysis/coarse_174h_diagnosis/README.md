# Coarse-sand174 h discrepancy audit

Entry point: `FINAL_DIAGNOSIS.md`. Phase1 decision: `PHASE_1_FINDINGS.md`. Detailed reports cover MRI, bottom gross exchange, interface/convection, sensitivity design and late-time physics. The accepted v12 source/results remain unchanged. This work belongs to branch `research/coarse-174h-discrepancy-audit`; it must not be merged into main automatically.

The six reviewed figure pages are collected in [COARSE_174H_AUDIT_FIGURES.pdf](results/COARSE_174H_AUDIT_FIGURES.pdf). File integrity is recorded in `AUDIT_MANIFEST.json`; visual inspection is recorded in `results/artifact_checks.json`.

## Reproduction levels

1. **Portable arithmetic/integrity verification:** `python verify_audit.py`. Requires Python, NumPy and pandas. Uses committed profile pairs, native face reductions, interval budgets and manifests. It verifies the reported reductions, not independently rerun experimental acquisition or174 h simulation.
2. **Offline re-extraction in the original project:** run `analyze_archives.py`, `thermal_comparison.py`, then `analyze_fluxes.py`. Their outputs stay in this analysis directory. They require the original experimental workbook/scan metadata, local v12 raw VTUs, and the independently archived v13 tar. These large source archives are deliberately not duplicated in the research branch. Source hashes and required paths are recorded. For original-project scripts, place this directory under `<project>/analysis/`; the repository's old `deliveries` package is not a complete raw archive.
3. **Native diagnostic reproduction:** on the authorized workstation with the unchanged v12 DuMuX/DUNE dependencies, put `build_replay.py`, `replay_main.cc`, `replay_member.hh`, `run_replay.py` into a new isolated directory. `build_replay.py` refuses to overwrite an existing source copy. Build, run `run_replay.py --pilot`, then `run_replay.py`. The separate `vertical_replay/` scripts select actual graded-grid planes and use seven checkpoints. Remote paths/compiler commands are explicit in build manifests; no package-install or shared-dependency change is implied. This reloads saved primary states and computes fluxes only—there is no Newton/time integration.

## Signs and units

- Bottom positive = outward from sample; gross in/out are both nonnegative magnitudes, computed **per face** before summation.
- Interface positive = F36→W3; advection and diffusion are signed and separately decomposed.
- Horizontal native flux positive = upward, with actual face heights recorded. Reconstructed cell LS velocities are separate diagnostics.
- Native component flux units are mol/s, liquid volume flux m³/s. Plotted salt uses58.44 g/mol NaCl equivalent.
- Accepted cumulative300s ledger is exact for the discrete trajectory; gross600s replay integrals are approximate10min quadrature. Their errors and20/60min sensitivity are tabulated. None is a grid/full-window solver-convergence study.
- Concentration figures use nominal evaporation time and whole-half1mm slabs. MRI corrected GV, recalibrated/edited concentration, liquid molarity and approximate observation operator are distinguished. No MRI-based experimental crystallization time is inferred.

## Included / excluded

Included: received task versions, audit scripts, diagnostic entry point/member patch/compiler manifest, pilot/full checks, seven-time face maps, reduced numerical histories, reports, figures and source hashes. Full raw states and original dependencies remain in their existing archives. The chapter-page extracts under `source_evidence` are local source-review aids; they need not be republished in Git. No credentials, monitor settings, old unrelated revisions or new full174 h sensitivities are part of this submission.

`REPLAY_LOG.md` records the repaired horizontal-plane selection and the removed plotting extrapolation. These are analysis-only changes. The original accepted binary SHA256 remains `6595025e48333062cfa05022d9f6d65670421d33f5fb6c92213c0a402a10b58e`.
