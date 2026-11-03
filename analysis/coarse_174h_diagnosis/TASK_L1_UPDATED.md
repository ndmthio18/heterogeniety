# Codex Task: Diagnose the Late-Time Coarse-Sand Concentration Discrepancy in the 174 h Heterogeneous Evaporation Simulation

## 1. Background and scientific objective

GitHub repository:

https://github.com/ndmthio18/heterogeniety

We have completed a 174 h simulation of evaporation-driven salt transport and precipitation in a heterogeneous porous medium consisting of coarse sand (F36) and fine sand (W3), using a three-dimensional DuMuX model.

The latest validated case is:

`20261102_cylinder_fixed_hydraulics_v12`

The main problem is that the simulation substantially underpredicts the coarse-sand salt concentration during late evaporation.

The experimental MRI profiles show that the coarse-sand concentration increases throughout much of the depth, with relatively small vertical variations. The model fails to reproduce the magnitude and temporal evolution of this increase.

From the archived comparison:

| Time | Experimental F36 mean | Model F36 mean |
|---|---:|---:|
| 60 h | 1.302 mol/L | 1.322 mol/L |
| 84 h | 1.478 mol/L | 1.329 mol/L |
| 96 h | 1.940 mol/L | 1.334 mol/L |
| 120 h | 2.172 mol/L | 1.354 mol/L |
| 144 h | 2.279 mol/L | 1.249 mol/L |
| 174 h | 2.450 mol/L | 1.234 mol/L |

These values refer to 3–37 mm depth averages.

Importantly, the model eventually produces an almost uniform coarse-sand concentration, but at an incorrect, much lower level. Therefore, the central problem is not merely vertical mixing. It may involve insufficient salt retention, incorrect boundary exchange, or incorrect redistribution between the two materials.

**Our scientific objective is to identify the physical and numerical origins of this discrepancy through reproducible evidence, rather than simply tuning parameters to match the experiment.**

## 2. Repository and execution rules

First, inspect the current repository and relevant archived results.

Important locations:

- `deliveries/RH0_fixed_174h_20261103/`
- `model_revisions/20261102_cylinder_fixed_hydraulics_v12/`
- `results/comparison/`
- `analysis/model_experiment_comparison_20261028/`
- `source/appl/problem.hh`
- `source/appl/spatialparams.hh`
- `source/appl/transport_fluidsystem.hh`

Read the existing reports, source files, experimental data, comparison scripts and provenance before modifying anything.

The GitHub repository is an analysis delivery archive, not a complete DuMuX execution environment. Check whether the original solver environment and full raw outputs are available locally or on the authorized remote workstation. Do not assume they are available.

Create a separate working branch:

`research/coarse-174h-discrepancy-audit`

Preserve all existing models, historical results, binary hashes, inputs, and archived data.

Place new analysis under:

`analysis/coarse_174h_diagnosis/`

Do not overwrite the original experimental data or accepted v12 output.

Do not merge into `main` automatically.

## 3. Task A — Audit the experimental MRI concentration evolution

This task must precede physical parameter calibration.

### A1. Reconstruct the experimental concentration histories

Read the archived MRI data and reproduce the concentration profiles for F36 and W3.

Evaluate at least:

0, 24, 48, 60, 84, 96, 108, 120, 144, 162, and 174 h.

For each time and material, calculate:

- Mean concentration over 3–37 mm.
- Standard deviation over depth.
- Concentration gradient with depth.
- Mean concentration in the 3–12, 12–28, and 28–37 mm bands.
- Changes relative to 0 h and 60 h.

Compare the experiment and numerical model using identical nominal depth intervals.

Distinguish the following clearly:

1. Experimental concentration derived from MRI.
2. Raw MRI signal.
3. Recalibrated concentration before manual corrections.
4. Model liquid-phase molarity.
5. Any observation-operator approximation.

Do not treat a spatially averaged model molarity as a direct measurement of total salt inventory.

### A2. Investigate the 84–96 h signal increase

The archived data show approximately:

- F36: +0.462 mol/L.
- W3: +0.374 mol/L.

Both materials exhibit an approximately 18% increase in mean raw MRI signal during the same interval.

Determine whether this increase may be explained by:

- Actual salt accumulation.
- A change in MRI calibration or normalization.
- Acquisition gain or reference-signal changes.
- Changes in ROI definitions.
- Differences between acquisition and nominal timestamps.
- Water-content-dependent MRI signal responses.

Check original experimental workbooks, available reference signals and the recorded scan metadata.

Do not conclude that the experiment contains an artifact merely because both materials increase simultaneously.

If necessary source data are missing, explicitly document what cannot be verified.

### A3. Independent experimental salt-budget plausibility test

Estimate the apparent dissolved salt inventory inferred from MRI.

Use the appropriate expression:

`n_dissolved = sum(C_i * phi_i * S_w,i * V_i)`

with consistent concentration and volume units.

Distinguish initial pore volume, actual liquid volume, and the MRI observation volume.

If experimental saturation fields are unavailable, construct physically justified bounds or scenarios rather than assuming saturation is exactly one.

Compare apparent inventory changes with the reservoir mass loss and independently known reservoir salt concentration.

In particular, investigate whether the 84–96 h apparent inventory increase can be supported by plausible salt supply and redistribution.

Do not claim a mass-balance violation unless the observation operator, liquid volume, and relevant salt reservoirs have been accounted for.

**Deliverable A:** `MRI_CONCENTRATION_AUDIT.md`, with reproducible CSV data, figures, uncertainties, and clearly stated unresolved questions.

## 4. Task B — Diagnose bottom-boundary salt exchange

This is the highest-priority numerical investigation.

The current implementation uses:

- `SupplyMode = DistributedReservoir`
- `FilterHydraulicResistance = 0`
- `Reservoir.Molarity = 1.0`
- `LevelAboveSandBottom = 0.02`

Inspect the bottom-boundary implementation in `problem.hh`, including the sign conventions and donor-state selection for inflow and outflow.

### B1. Separate gross inflow and outflow

The current budget records net component exchanges. This is insufficient to determine whether high-concentration water exits the coarse sand while dilute reservoir water enters elsewhere.

For each accepted time or suitable diagnostic interval, calculate separately:

- Gross water inflow through the bottom.
- Gross water outflow through the bottom.
- Gross NaCl inflow.
- Gross NaCl outflow.
- Net water and NaCl exchange.
- Salt concentration of outgoing liquid.
- Spatial distribution of inward/outward bottom fluxes.

Separate F36 and W3.

Do not calculate gross inflow/outflow by taking the absolute value of an already integrated net flux.

If the current outputs lack the necessary face-resolved information, add minimal diagnostic instrumentation to a separate source revision and rerun only what is necessary.

Preserve the original physical equations and numerical settings.

### B2. Diagnose the late-time coarse-sand salt loss

Investigate the intervals:

0–24, 24–60, 60–84, 84–96, 96–120, 120–144, and 144–174 h.

Determine whether downward dense-brine transport causes salt to leave the sample through the bottom boundary.

Particularly examine 120–174 h, when the modeled coarse-sand concentration decreases.

Calculate the fraction of coarse-sand salt exported through the bottom, retained within the coarse sand, and exchanged with the fine sand.

Check whether bottom inflow and outflow occur simultaneously in different spatial regions.

Compare the timing of these processes with the coarse-sand concentration trend and reconstructed vertical velocities.

**Deliverable B:** `BOTTOM_BOUNDARY_FLUX_AUDIT.md`, including signed and gross flux histories, spatial maps, and a complete salt balance.

## 5. Task C — Quantify coarse–fine interface transport and convective redistribution

The current 174 h model salt budget indicates:

- Coarse-sand net bottom salt supply: 1.573 g.
- Net coarse-to-fine salt exchange: 1.342 g.
- Coarse-sand net salt accumulation: 0.231 g.

Approximately 85% of the net bottom salt supply to F36 is offset by net transfer to W3.

We need to understand the mechanisms producing this redistribution.

### C1. Interface transport decomposition

Extract and verify:

- Advective salt transfer F36 → W3.
- Advective salt transfer W3 → F36.
- Diffusive transfer in both directions.
- Net interface salt exchange.
- Water exchange across the interface.
- Spatial distribution of interface fluxes.

Separate instantaneous signed contributions from time-integrated gross contributions.

Use the actual finite-volume face fluxes and correct face areas.

Reconcile the results with the original model's accepted salt-budget ledger.

### C2. Density-driven convection diagnostics

Analyze the F36 fields at:

24, 60, 84, 96, 120, 144, and 174 h.

Quantify:

- Vertical liquid velocity.
- Upward and downward flow regions.
- Density and concentration anomalies.
- Horizontal concentration heterogeneity.
- Concentration–vertical-velocity correlation.
- Vertical advective salt transport.
- Lateral transport across the material interface.

Evaluate whether convection primarily redistributes salt internally or transports salt toward boundaries where it is subsequently lost.

Do not infer actual experimental flow velocities from MRI concentration maps alone.

### C3. Separate mean-concentration and profile-shape errors

For each time, decompose the concentration comparison into:

- Mean concentration bias.
- Difference in vertical profile shape.
- Horizontal heterogeneity in the model.
- Differences in concentration growth rate.

Explain why the model approaches a nearly uniform F36 concentration at 144–174 h while the experiment continues to increase.

Do not interpret successful numerical conservation as validation of the underlying physics.

**Deliverable C:** `INTERFACE_AND_CONVECTION_AUDIT.md`, including flux decompositions, concentration evolution, and a ranked set of hypotheses.

## 6. Task D — Design controlled boundary-condition sensitivity simulations

Only begin after Tasks A–C have established a defensible baseline.

Our leading hypotheses are:

H1: The bottom boundary allows excessive loss of dense, salt-rich liquid.

H2: The model overestimates net salt transfer from coarse to fine sand.

H3: The modeled evaporation partition and liquid replenishment differ from the experiment.

H4: The modeled density-driven convection has incorrect strength, spatial organization or connectivity.

H5: Part of the apparent experimental discrepancy is related to the MRI observation operator.

Design controlled numerical comparisons to distinguish these hypotheses.

Potential experiments include:

**D1. Bottom hydraulic resistance**

Evaluate physically meaningful nonzero filter/interface hydraulic resistance, while maintaining the same reservoir chemistry and water level.

Report how the modified boundary affects water supply, bottom outflow, concentration, interface exchange and evaporation.

Do not choose resistance values solely to minimize concentration RMSE.

**D2. Reservoir connection geometry**

Assess the difference between distributed bottom exchange and the actual experimental inlet/filter geometry.

Important: the present source rejects `CentralAperture` for the cylinder. Do not simply switch this parameter. Any alternative must be implemented using physically correct three-dimensional face geometry and independently tested.

**D3. Material-interface exchange**

Analyze whether uncertainties in material hydraulic functions and relative permeability affect lateral exchange.

Avoid simultaneously changing multiple unrelated parameters.

**D4. Density-driven flow and transport**

Test the physical sensitivity to density effects and effective transport properties through clearly isolated scenarios.

Do not introduce artificial mechanical dispersion or increase molecular diffusivity solely to produce a better concentration match.

For each sensitivity, specify the hypothesis, parameter change, physical justification, expected signature, and falsification criterion before running it.

First conduct inexpensive short tests and verify the model remains conservative. Do not automatically launch multiple full 174 h HPC simulations.

**Deliverable D:** `SENSITIVITY_MATRIX.md`, accompanied by verified short-run results where possible.

## 7. Task E — Evaluate late-time evaporation and precipitation physics

The baseline v12 model uses fixed porosity and intrinsic permeability, with equilibrium precipitation retained.

At 174 h, the equivalent solid-volume inventory variable becomes much larger than physically admissible geometric pore occupancy.

Therefore, do not interpret v12 as a physically validated pore-blockage or salt-crust model.

Analyze:

- Why the simulated reservoir loss exceeds the experiment after 60 h.
- Whether the current equivalent gas-film model overestimates late-time vapor transport.
- Whether surface salt accumulation could change local evaporation resistance.
- Whether the coarse/fine evaporation partition changes after precipitation.
- Whether nonisothermal effects might influence the late-time discrepancy.

Use existing independent nonisothermal or vapor-transfer revisions if accessible. Preserve their provenance and do not mix results from different model revisions without explicit qualification.

Separate physical hypotheses from unvalidated implementation assumptions.

Do not add a new crust model or perform arbitrary parameter fitting during this audit.

**Deliverable E:** `LATE_TIME_PHYSICS_ASSESSMENT.md`.

## 8. Numerical and scientific validation requirements

Maintain the accepted baseline as a reference:

- Temperature: 293.15 K.
- RH: 0.
- Equivalent gas-film thickness: 8.100162 mm.
- F36 porosity: 0.40.
- W3 porosity: 0.36.
- F36 intrinsic permeability: 7.819185772e-12 m².
- W3 intrinsic permeability: 3.203409878e-14 m².
- Pre-equilibration: 2 h.
- Evaporation: 174 h.
- Baseline mesh: 30,720 cells.
- Maximum time step: 300 s.

For any altered case, record all changed parameters and the reason for each change.

Verify conservation of water, dissolved salt, solid salt, and material-wise total salt.

Verify that the sum of bottom and interface contributions reproduces changes in material salt inventory.

Before interpreting small changes, check temporal and spatial numerical sensitivity at appropriate checkpoints.

If modifying code, add tests for sign conventions, gross-versus-net flux integration, face geometry, and budget closure.

Do not silently alter physical equations, numerical tolerances, initial states, experimental processing, or simulation times.

Do not disturb existing HPC jobs, change shared dependencies, or overwrite completed runs.

## 9. Final deliverables and decision criteria

Create:

`analysis/coarse_174h_diagnosis/FINAL_DIAGNOSIS.md`

The final report must include:

1. A concise explanation of what the 174 h simulation correctly and incorrectly predicts.
2. Quantitative comparison of F36 and W3 concentration evolution.
3. Experimental MRI signal and salt-inventory audit.
4. Gross and net bottom salt fluxes.
5. Coarse/fine interface transport decomposition.
6. Density-driven flow diagnostics.
7. A ranked list of candidate causes, explicitly distinguishing observed evidence, model-derived results, and untested hypotheses.
8. The minimum set of model modifications needed for the next controlled tests.
9. A proposed validation sequence with clear GO/NO-GO criteria.
10. Reproducible figures, CSV outputs, scripts, execution logs, source revisions and input hashes.

Suggested comparison metrics:

- F36 mean concentration error.
- F36 concentration profile RMSE.
- F36 vertical concentration gradient error.
- W3 concentration profile RMSE.
- Reservoir-loss error.
- F36/W3 salt inventory and exchange rates.
- Water and total-salt conservation residuals.

A modification must not be declared successful solely because F36 concentration improves while evaporation, W3 concentration, or overall conservation becomes worse.

## 10. Execution protocol

Start immediately with the existing archived results and Tasks A–C.

Use the saved data before adding instrumentation or restarting the solver.

Clearly identify which tasks can be completed entirely offline and which require the full original DuMuX environment or experimental source files.

After Tasks A–C, write an interim report:

`PHASE_1_FINDINGS.md`

Include the three strongest supported explanations of the discrepancy and the most discriminating numerical tests.

You may prepare Task D/E code and inexpensive diagnostic cases in an isolated revision when the physical assumptions and required environment are verified.

Do not launch long 174 h parameter sweeps or substantially change the physical model without presenting the Phase 1 findings and the proposed test matrix for review.

Commit validated work to the research branch with clear, focused commits. Push only if authorized by the existing repository workflow. Never modify the original accepted v12 archive.

**Priority: identify why the model fails to accumulate salt in coarse sand despite predicting density-driven convection. Establish the cause through transport budgets and independent evidence before attempting calibration.**