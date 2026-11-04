# Numerical verification

## Passed

- Gate A geometry: 768 lower faces, exact 4 mm nominal circle area, 4.5 mm six-layer filter and source/input hashes recorded.
- Gate B boundary transport: four bidirectional probes passed; hydraulic-potential residual `2.05e-7 Pa`; salt donor and enthalpy relative errors below `1.9e-16`.
- Gate C original-output short run: completed 7,800 s (2 h pre-equilibration plus 0.167 h evaporation). Maximum relative residuals were water `5.83e-14`, total salt `2.94e-14`, F36 `1.27e-13`, W3 `8.18e-14`, and energy `1.64e-10`. Temperature range was 291.881--293.15 K. Complementarity residual was `1.10e-30`; minimum numerical solid volume fraction was `-1.04e-32`.
- Gate D hourly VTK fallback: final state and all listed physical/compact tables were SHA-identical to every-checkpoint output.
- Gate C formal Slurm rerun: jobs `16293235` (six layers) and `16293236` (twelve layers) completed on `cnmix` with exit code `0:0`. Six-layer peak RSS was 273,784 kB and twelve-layer peak RSS was 381,316 kB. The formal six-layer residuals reproduced the diagnostic values above; the twelve-layer maximum water/salt material residual was below `3.70e-13` and its energy residual was `1.64e-10`.
- Gate D detailed-face thinning: the formal sparse-face run and dense-face reference had byte-identical final state, water/salt/thermal/mineral/material/native-flux histories, and compact profiles. `film_faces.csv` decreased from 10,424,694 to 608,431 bytes.
- Vertical filter screen: six versus twelve filter layers differed by at most `2.102e-6` relatively across the reported terminal scalar metrics; the maximum compact-profile concentration difference was `3.55e-8 mol/L`.

## In progress or not demonstrated

- The twelve-layer comparison addresses vertical filter resolution only and is not a full-window convergence study.
- True local radial refinement around the approximately 4 mm opening is not yet demonstrated. Exact fractional face integration is not a substitute.
- Formal sequential Slurm jobs `16293333`--`16293336` are queued for 1/2/4/8-thread equivalence and scaling. Allocation alone will not be reported as acceleration.
- Neither 174 h primary case is admitted or complete.
