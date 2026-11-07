# Repair log

174 h release attempt 01 (Slurm 16309384) failed during input parsing, before solving: Benchmark.FaceOutputInterval appeared twice because the accepted remote input already contained this parameter. The original failed directory and logs remain at /WORK/hulm_work/zhixin/Greal_external_crust_release_20261106.

The generator now replaces an existing FaceOutputInterval instead of inserting a duplicate. Attempt 02 is isolated at /WORK/hulm_work/zhixin/Greal_external_crust_release_20261106_r02. Binary SHA256 is unchanged: 4f6ef0c672e5e5c04e376c815e0c29f281a41f36359ce0c116de6000bb26df6d. Slurm 16309385 was observed RUNNING and accepted its first 10 s timestep. No physical or solver parameter was changed in the repair.

Attempt 02 later stopped after 75 h evaporation because the HPCC account file-count quota prevented further VTK output. This was an output/storage failure, not an accepted 174 h result. Its logs and lightweight 75 h diagnostics were retained.

Because no verified restart state existed, the calculation was restarted from the original initial state on Frodo in `/temp/zhixin/Greal_external_crust_174h_frodo_20261106`. The source physics, input parameters, timestep controls and tolerances were unchanged. The Frodo-native executable SHA256 was `99775343b964856a5a3820cf5ed32e5603273783c8e269ffdd628ad5412028ee`. The run completed 174 h evaporation with return code 0 on 2026-11-06. This migration and completion do not retroactively qualify the outstanding numerical gates.
