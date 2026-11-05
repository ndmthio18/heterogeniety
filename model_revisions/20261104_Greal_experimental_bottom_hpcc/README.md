# G-real experimental-bottom campaign

This isolated revision tests the full 3-D nonisothermal F36/W3 cylinder with an explicit 4.5 mm P3 filter and an approximately 4 mm central inlet. It does not replace any accepted B/G/v13 executable or result.

Primary cases are `Greal-75` (7.5 mm gas film) and `Greal-81` (8.100162249880822 mm). Both use RH=0, 293.15 K initial/ambient/reservoir temperature, 2 h pre-equilibration and 174 h evaporation. The measured P3 mean saturated permeability is `5.30e-12 m2`; inherited filter retention and thermal properties remain provisional.

The campaign is gated. Geometry/source, hydrostatic/boundary transport, short coupled conservation, reduced-output equivalence, multicore equivalence/performance and HPCC storage/admission must pass before production. A completed process is not an accepted scientific result until its endpoint, budgets and hashes pass.

## Evidence boundary

- Exact polygon/circle overlap conserves the nominal inlet area but does not prove convergence of the local radial pressure field.
- The current 4 mm opening spans only about 1.6 maximum bottom-face equivalent diameters; local spreading remains under-resolved until a targeted refinement passes.
- Saturated filter permeability alone does not validate the inherited capillary, relative-permeability or thermal functions.
- Film thickness is a calibrated effective heat/mass-transfer parameter. Agreement in evaporation does not independently validate ambient humidity or the bottom boundary.
- MRI dissolved-salt observations and simulated dissolved-plus-solid salt inventory are not interchangeable.

See `PROGRESS.md` at project root for current execution state.

## Execution status (2026-11-05)

Geometry, boundary transport, formal short-coupled conservation, sparse-output
equivalence, six/twelve-layer vertical screening, storage admission, and the
formal 1/2/4/8-thread Slurm benchmark passed. Greal-75 (`16293418`) and
Greal-81 (`16293419`) both reached 2 h pre-equilibration plus 174 h evaporation
and exited 0. Endpoint, water/salt/material/energy budgets and final file lists
passed. The authoritative 6.5 GB remote archive contains 754 files and has
SHA256 `9c55017bc712067afc6a32b0e801725364bfe1f38279468b25f281e937c9cf9f`;
only the verified compact data and hash lists are stored locally.

Greal-81 is the better full-window member of this pair: its 1--174 h reservoir
loss is 52.4057 g versus 51.52 g measured (+1.719%), compared with 56.0068 g
(+8.709%) for Greal-75. Neither result is an independent validation: Greal-81
still misses the preset 1% endpoint tolerance, and both modeled interval-rate
curves decline less strongly than the experiment.
