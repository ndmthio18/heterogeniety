## 2. Methods and provenance

### 2.1 Execution environment
- liqin, CPU5 only (`taskset -c 5`), `nice 10`, OMP/OpenBLAS/MKL/TBB threads 1, one solver at a time. Controller `remote/controller.py` (flock single instance) runs the ordered `queue.json` serially; `remote/run_case.py` runs one case: resource gates before launch (MemAvailable ≥8 GiB, scratch ≥8 GiB + expected size, home ≥2 GiB — waits, never fails, while short), wall limit (6 h coarse/medium, 12 h fine), peak RSS from `/proc/<pid>/status` VmHWM, closed VTU frames gzip-archived with raw-SHA256 = decompressed-SHA256 before the raw copy of that new frame is removed, `run_manifest.json` with binary/input/mesh hashes, acceptance validation.
- Remote tree `/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_verification_v11` (scripts, inputs, meshes, status, reduced analysis); raw runs `/tmp/zhixin_verification_v11_20261030/runs/<case>`.
- Python on liqin: `/home/zhixin/micromamba/envs/vasca311/bin/python3` (Python 3.11.13, NumPy 2.1.3, pandas 3.0.2). System Python was not used for analysis.
- No compilation was performed by B (the handoff binary is used as delivered and hash-verified), so the shared compile lock was never taken.

### 2.2 Pre-handoff engineering tests (frozen v08 binary c9145e42…, not effect checks)
| test | purpose | result |
|---|---|---|
| RT_medium_v08bin | runner/pipeline regression vs v08 Dry_trial02_r02 to 1 h evaporation | budget.csv rows bitwise identical (57 rows); raw VTU SHA256 identical at 0/2/3 h; 12.5 min wall; peak RSS 0.22 GiB |
| RT_coarse_v08bin | new-mesh solver geometry audit, 2 h zero-evaporation stationarity, timing | solver audit passed (contact 0.002 m², sin non-orth 4e-13); pre-period salt/water drift ≤2e-15 relative, S=1; 1 h film water 0.35305 g vs medium 0.35302 g; 4.0 min wall; 0.12 GiB |
| RT_fine_v08bin | same for fine mesh; memory/time projection | see §2.3 |
