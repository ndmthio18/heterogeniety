# Accelerated nonisothermal v13 bottom-boundary campaign

See TASK.md, METHOD.md, BASELINE_VERIFICATION.md, BOUNDARY_IMPLEMENTATION.md and CASE_MATRIX.csv. This is an authorized running research campaign; FINAL_COMPARISON.md is explicitly pending. RUN_STATUS.csv and remote_status_latest.json are timestamped snapshots, not live status.

Source_baseline is the exact frozen accelerated source; source_filter contains isolated explicit-filter changes. Input manifests protect all case inputs and meshes. Build scripts record the pinned remote dependency paths and compiler commands; full DuMuX/DUNE/runtime libraries and compiled binaries are not bundled. Build/relocation manifests record hashes. The source patches and preserved failed test attempts explain changes.

Repository omits raw VTU, transport tar, executable/runtime libraries and scalar-field NPZs. For a fresh deployment, run `python prepare_reference.py <accepted-v13-final_174h_delivery.tar>` using the separately preserved, hash-verified reference archive (SHA716288ecba754a483d4faa3e34fbdb0a400cb38b416272b24f4b024cde3f7ec3). This reconstructs the ten comparison NPZs and verifies each selected member. Original MRI and experiment CSVs are retained unchanged. Host-specific build/deployment scripts require the documented pinned dependencies; they are not standalone installers.

Current launch: baseline19181 passed; B short19182 active, full19183 pending; G probe19191 passed, dynamic gates19187/production19188–19190 held. Initial324-file backup passed. Full174h results and native replay/visual comparison remain pending. Monitor v13-b-g checks every2h.
