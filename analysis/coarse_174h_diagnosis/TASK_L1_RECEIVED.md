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

Assess the difference between distributed bottom exchange and the actual