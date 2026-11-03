# Task: Parallel Bottom-Boundary Sensitivity Campaign Based on Accelerated v13

## Objective

Implement, verify, and run a parallel bottom-boundary sensitivity campaign for the F36/W3 heterogeneous evaporation experiment.

Use the **accelerated, nonisothermal v13 DuMuX model** as the physics baseline.

Execute independent cases on the `sal` server using multiple CPU cores, with strict process isolation and resource controls.

The scientific objective is to determine whether the real experimental bottom connection — a 4.5 mm P3 porous filter plate with a central lower inlet — can explain the underprediction of late coarse-sand concentration.

Repository:

https://github.com/ndmthio18/heterogeniety

Latest audit branch:

`research/coarse-174h-discrepancy-audit`

Audit commit:

`a34beee799de1fb7b3a916edc843793e7c664404`

Read `FINAL_DIAGNOSIS.md`, `BOTTOM_BOUNDARY_FLUX_AUDIT.md`, and `SENSITIVITY_MATRIX.md` before implementation.

## Phase 0 — Identify and freeze the accelerated v13 baseline

Locate the current accelerated nonisothermal v13 implementation in the original project workspace.

Do not assume that v14 or another optimization branch is equivalent to accelerated v13.

Record:

- Exact source directory and revision.
- Executable SHA256 and dependency versions.
- Physics and numerical changes relative to accepted v13.
- Acceleration strategy.
- MPI/OpenMP/threading support.
- Previously measured execution time and peak memory.
- Validated baseline inputs and output hashes.

The independently accepted v13 reference includes:

- Reservoir solution loss: 51.947836 g over 1–174 h.
- F36 3–37 mm mean concentration: 1.230835 mol/L.
- W3 3–37 mm mean concentration: approximately 2.162 mol/L.
- Final solid inventory: 0.226441 g.

Perform a zero-change regression against the accepted v13 results.

Check temperature, pressure, concentrations, saturation, water/salt/energy budgets, interface transport, precipitation and solution loss.

If accelerated v13 differs physically from accepted v13, stop production launches and identify the cause. Do not silently substitute another revision.

Freeze the verified executable and source manifest.

## Phase 1 — Implement bottom-boundary variants

Create a separate revision/campaign workspace. Never overwrite the accepted v13 or v12 results.

### Group B: Equivalent filter resistance

Retain the original distributed-reservoir geometry.

Use the existing resistance formulation, with correct dimensioned units.

Compute the representative initial coarse-sand bottom half-cell hydraulic resistance:

`R_ref = mu_ref * d_ref / (K_F36 * kr_ref)`

Define four exploratory cases:

- B0: `Rf = 0`
- B1: `Rf = 0.1 * R_ref`
- B2: `Rf = 1.0 * R_ref`
- B3: `Rf = 10.0 * R_ref`

Use one common physical filter resistance across both materials for each case, rather than scaling F36 and W3 independently.

Record the actual resistance in Pa·s/m, the reference viscosity, reference distance, relative permeability and any temperature dependence.

These values are diagnostic brackets, not measured P3 filter properties.

Keep the reservoir water level and inlet NaCl concentration unchanged.

### Group G: Explicit filter and central inlet

Implement the actual structural arrangement:

Reservoir → central lower port → porous filter → F36/W3 sand.

The filter must:

- Cover the entire sand bottom.
- Have thickness 4.5 mm.
- Permit lateral and vertical liquid transport.
- Have conservative liquid/NaCl coupling with the sand.
- Include physically consistent pressure and solute interfaces.
- Preserve the existing sand geometry and material interface.

Use an independently specified filter porosity and permeability. If unavailable, state explicit exploratory assumptions.

Initially assign a common filter permeability that produces a representative through-thickness resistance comparable to B2. Keep it fixed across the geometric sweep.

Implement:

- G1: central port diameter 2 mm.
- G2: central port diameter 5 mm.
- G3: central port diameter 10 mm.

These are hypothetical dimensions, not experimentally verified.

If the lower plenum geometry is unknown, use a clearly documented simplified port-at-filter-bottom geometry, rather than claiming to reconstruct the actual plenum.

Do not activate the existing cylinder `CentralAperture` switch without replacing its unsupported geometry logic.

Do not double-count filter resistance by imposing both an explicit filter and its equivalent Robin resistance.

Ensure the additional filter volume and salt inventory are included in conservation checks, and report sand-only inventories separately.

### Required implementation checks

Verify:

1. Correct 3D port area and filter geometry.
2. Consistent hydrostatic equilibrium.
3. Flow and salt-flux continuity.
4. Correct bidirectional inflow/outflow donor states.
5. Correct heat-transfer coupling for nonisothermal cases.
6. Water, NaCl and energy conservation.
7. The correct zero-resistance/distributed-boundary limit.

## Phase 2 — Parallel computing on sal

Check the actual `sal` system first:

- CPU topology and available cores.
- Available memory and scratch disk.
- Current workload and existing users' jobs.
- Job scheduler availability.
- Verified MPI or OpenMP support of the solver.
- Peak RAM and execution time of a representative case.

Use process-level parallelism unless solver-level multicore scaling is actually verified.

**Important:** Multiple independent serial DuMuX runs distributed across CPU cores are valid multicore utilization. Do not assume that setting `OMP_NUM_THREADS` or launching `mpirun` automatically makes a serial solver faster.

If a scheduler is available, use its job array and resource allocation mechanism.

Otherwise build a bounded local queue with:

- Independent process directories.
- Distinct CPU affinities where appropriate.
- Conservative thread limits.
- Controlled memory and disk usage.
- Individual PID/status/log files.
- No oversubscription.
- No interference with existing unrelated simulations.

Choose concurrency from measured resource availability. As an initial upper safety bound, do not consume more than approximately 70% of legitimately available CPU capacity or memory; respect any stricter cluster policies.

Do not kill, alter, or suspend unrelated jobs.

### Launch strategy

Begin the B0–B3 cases concurrently once their short regression tests pass.

Develop and test G1–G3 in parallel with the B runs. Do not block Group B while geometry development continues.

For every case:

1. Complete hydrostatic and two-hour pre-equilibration tests.
2. Run a short evaporation test and verify conservation.
3. Run through relevant early/intermediate checkpoints and compare against B0.
4. If all gates pass, queue the complete 174 h case using the approved resource budget.

Do not attempt to restart from saved VTU fields unless a physically and numerically verified restart mechanism exists.

Retain all failure information. Do not silently change tolerances, parameter values or time-step settings to make a case finish.

## Phase 3 — Automatic diagnostics for every case

At minimum, retain outputs at:

24, 60, 84, 96, 120, 144 and 174 h.

Calculate:

- F36/W3 mean concentration and depth profiles.
- F36/W3 concentration RMSE against the archived MRI profiles.
- Vertical concentration gradients.
- Gross bottom water inflow and outflow.
- Gross bottom salt inflow and outflow.
- Concentration of outgoing bottom solution.
- Net bottom salt supply.
- F36→W3 and W3→F36 interface transport.
- Advective and diffusive salt contributions.
- Downward/upward velocities and spatial concentration anomalies.
- Dissolved/solid/total salt inventories.
- Reservoir solution loss and interval evaporation rates.
- Water, salt and energy conservation.
- Runtime, CPU usage and memory consumption.

Use native finite-volume face fluxes, not only reconstructed cell velocities.

Keep the original MRI concentration series unchanged.

Correct the MRI audit's previously identified echo-time statement: E39 has TE=4.0 ms and E41 TE=4.6 ms. Preserve acquisition and nominal-clock distinctions. Do not fit model parameters to an unresolved observational discrepancy.

## Phase 4 — Compare mechanisms rather than optimize RMSE alone

Analyze three central scientific questions.

**Question 1: Does filter resistance reduce excessive coarse-bottom recirculation?**

Determine how gross in/out, net salt supply, F36 retention, and F36→W3 transfer change with resistance.

**Question 2: Does the central inlet geometry change the hydraulic partition?**

Compare filter-top pressure, local flow distribution, coarse/fine bottom supply, and horizontal filter flow for G1–G3.

Determine whether a uniform equivalent filter resistance is sufficient.

**Question 3: Can a modified bottom boundary reproduce progressive coarse-sand enrichment without damaging other observables?**

Compare both sand concentration histories, total evaporation, precipitation, and conservation simultaneously.

Do not declare a case better because F36 concentration alone improves.

## Phase 5 — Results, execution monitoring and version control

Create an isolated campaign folder in the original project, for example:

`model_revisions/20261103_v13_bottom_boundary_campaign/`

Include:

- `BASELINE_VERIFICATION.md`
- `BOUNDARY_IMPLEMENTATION.md`
- `CASE_MATRIX.csv`
- `RESOURCE_PLAN.md`
- `RUN_STATUS.csv`
- `CPU_MEMORY_BENCHMARK.md`
- `FINAL_COMPARISON.md`
- Case-specific inputs, hashes, logs and diagnostics.

Include a machine-readable status record showing which cases are pending, running, completed, failed or rejected by a validation gate.

Do not label a queued or partial simulation as completed.

Generate comparison figures using consistent time bases, concentration units and axes.

Maintain an independent research branch. Commit source changes, configuration and lightweight diagnostic outputs after verification. Do not commit large raw VTU archives or modify existing accepted results.

## Execution authorization

The user has authorized preparing and running this parallel bottom-boundary sensitivity campaign on `sal`.

Proceed through implementation, numerical gates and resource-controlled job submission without stopping merely to request another planning confirmation.

If an essential source directory, remote login, cluster authorization or physical dependency is unavailable, document the blocker and complete all executable preparation rather than inventing a result.

Report the actual case/job identifiers and status after submission. Never report a case as launched unless the remote process or scheduler confirms it.

The primary scientific objective is to determine whether bottom-filter resistance and central-port geometry change coarse-sand salt retention sufficiently to explain the late experimental concentration increase.