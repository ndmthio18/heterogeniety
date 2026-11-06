# HPCC resource report

Preflight on 2026-11-06 found approximately 290 idle `cnall` nodes and 4.9 PB
free capacity on `/WORK`. Existing unrelated user jobs were not modified.
The scheduler's `RealMemory=1 MB` metadata does not describe physical node
memory and rejects explicit normal memory requests; this campaign follows the
accepted Greal workflow by omitting `--mem` while recording `/usr/bin/time -v`
peak RSS for every case.

Each simulation is one MPI rank with eight DuMuX computational threads and
OMP/BLAS set to one thread. M0 uses two concurrent regression jobs. M1 uses
four concurrent independent jobs. Later matrices default to four concurrent
cases and may increase to six only after a fresh admission check. Login nodes
host only low-resource submission/monitoring scripts, never the solver.

Remote root:
`/WORK/hulm_work/zhixin/Greal81_coupling_regime_20261106`

Frodo build root:
`/temp/zhixin/Greal81_coupling_regime_20261106`
