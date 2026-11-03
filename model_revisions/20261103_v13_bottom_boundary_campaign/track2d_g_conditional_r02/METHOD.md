# Conditional 2D G1–G3 production

The user authorized simultaneous full-duration 2D G calculations on 2026-11-03. This isolated attempt preserves the original failed `G1_refined` gate and does not relabel it as passed.

The original production-grid G1–G3 short cases, hydrostatic checks, boundary probes, and G1 half-timestep case passed. The doubled-resolution G1 screen failed at evaporation onset because the Newton residual plateaued at 1.04–1.09e-10, slightly above the fixed 1e-10 threshold, while relative state shifts were about 1e-15. No tolerance, timestep, retry limit, mesh, physics, filter property, inlet mapping, or fit parameter is changed here.

G1–G3 run from the original initial conditions using the frozen 2D executable and inputs in three independent directories. They are explicitly labeled `conditional_unaccepted_refined_grid_gate`. Their fields may be used to inspect sensitivity and prepare figures, but they cannot support a grid-accepted quantitative conclusion until the failed spatial screen is resolved.

The three cases start simultaneously on Frodo physical CPU IDs 3, 10, and 11, one thread per process, nice 10. Existing 3D runs use CPUs 4–8 and remain untouched. Total heavy occupancy is eight of twelve physical cores. Initial admission requires at least 12 GiB available memory and 80 GiB free disk. Each solver retains the existing 4 GiB scratch guard and 48 h wall limit. Raw and failed outputs remain preserved and are backed up with SHA256 verification.

After all three cases reach 174 h and pass their per-case water, salt, energy, physical-state, and field-ledger checks, the existing 2D MRI/profile figure is regenerated with B0–B3 and conditional G1–G3 clearly distinguished. Completion of a production run does not repair the outstanding refined-grid evidence gap.
