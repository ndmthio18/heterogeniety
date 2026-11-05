# Analysis environment

2026-11-05: HPCC default Python lacked pandas/matplotlib. An isolated venv was created in the new audit directory. Unpinned installation selected a pandas source build and failed against GCC 4.8.5. Repaired by installing binary wheels only: numpy 1.26.4, pandas 2.2.3, matplotlib 3.8.4. Inventory analysis then exited 0. Accepted solver inputs, binaries and outputs were not changed.

Analysis QA: corrected face material split from x=0 to the actual x=0.025 m before interpreting the screening results. Reran surface integration. Corrected descriptive profile weighting from liquid volume to overlap-weighted bulk volume after reading campaign_diagnostics.hh; the original C_volume_mean_M values and all calculated MRI errors are unchanged. Selected VTU lookup now uses PVD timestamps. Duplicate diagnostic rows occur at the pre-equilibration boundary; clipped evaporation-window integration assigns them zero duration, so no duplicated flux contribution enters the reported 0–174 h integrals.

The film_faces equilibrium vapor-pressure diagnostic uses reference temperature; actual filmWaterFlux_ uses local surface temperature and mean film temperature. The diagnostic was not inverted to estimate temperature. Selected native T fields provide temperature evidence. No accepted source or output was repaired or modified.
