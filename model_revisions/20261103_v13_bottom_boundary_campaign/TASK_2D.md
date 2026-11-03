# Research Task: Parallel 2D and 3D Bottom-Boundary Investigation Using Accelerated Nonisothermal v13

## 1. Scientific objective

We are studying evaporation-driven salt redistribution in a heterogeneous porous medium consisting of F36 coarse sand and W3 fine sand.

Repository:

https://github.com/ndmthio18/heterogeniety

Latest audit branch:

`research/coarse-174h-discrepancy-audit`

Audit commit: `a34beee799de1fb7b3a916edc843793e7c664404`

The latest numerical audit has established that the current model produces density-driven downward convection in F36 but fails to reproduce the experimentally observed progressive salt enrichment.

### The primary experimental phenomenon

Ali's experimental Chapter 4, particularly Figure 4.7d, shows that the average Na concentration in F36 increases throughout almost the entire sample depth during evaporation.

This includes the upper, middle and lower regions of F36.

The experimental concentration profiles become substantially enriched while remaining relatively uniform over depth compared with the strong near-surface concentration gradients in W3.

In contrast, our current nonisothermal v13 simulation predicts an F36 concentration that remains near 1.2–1.35 mol/L during late evaporation.

At 174 h:

- Experimental F36 mean concentration (3–37 mm): approximately 2.45 mol/L.
- Nonisothermal v13 F36 mean: approximately 1.23 mol/L.

**Our central objective is to determine whether a more realistic representation of the bottom hydraulic boundary allows the model to reproduce the experimentally observed progressive, depth-wide concentration increase in F36.**

This is not merely a study of salt accumulation at the bottom.

An increase confined to a thin bottom layer is insufficient. We need to investigate enrichment throughout the coarse-sand domain.

The proposed physical chain is:

Surface evaporation → salt concentration increase → density-driven downward redistribution → salt retention throughout F36 → progressive concentration increase with depth remaining relatively uniform.

The bottom-boundary modifications should test whether the current model loses or redistributes too much salt through excessive bottom recirculation and lateral transfer to W3.

## 2. Existing evidence

The previous audit quantified:

- F36 gross bottom salt inflow: approximately 6.889 g.
- F36 gross bottom salt outflow: approximately 5.317 g.
- F36 net bottom salt input: approximately 1.573 g.
- F36 net salt transfer toward W3: approximately 1.342 g.
- F36 retained salt increase: approximately 0.231 g.

During 120–174 h, F36 continues receiving net salt through the bottom, but interface salt export exceeds bottom supply, resulting in declining F36 salt inventory.

Therefore, the problem involves both bottom exchange and F36–W3 lateral transport.

The independent nonisothermal v13 model reduces the reservoir-loss error from approximately +11.06% to +0.83%, while leaving F36 concentration nearly unchanged.

This indicates that correcting evaporation alone does not solve the late-time F36 concentration discrepancy.

We must investigate the hydraulic and solute-transport pathways.

## 3. Experimental bottom geometry

According to Chapter 4, Section 4.2.1 and Figure 4.1:

- Cylinder diameter: 50 mm.
- Sand height: 40 mm.
- F36/W3 separated by a vertical interface.
- Bottom porous filter: P3, 4.5 mm thick.
- External reservoir connected through a central lower inlet.
- Reservoir solution: initially 1 mol/L NaCl.
- Reservoir water level: approximately 20 mm above the sand bottom.

The current model instead connects the full sand bottom directly to the distributed reservoir boundary with no additional filter resistance.

The actual inlet diameter, filter permeability, and lower connection geometry must be checked. Do not present assumed values as measured experimental parameters.

## 4. Preserve existing simulations

All accepted v12 and v13 simulations, data and source versions must remain unchanged.

Do not overwrite or delete existing 3D results.

Do not interfere with currently running unrelated simulations.

Create a new isolated project revision, for example:

`model_revisions/20261103_v13_bottom_boundary_campaign/`

Use separate subdirectories for 2D and 3D simulations.

Keep complete source, executable, input and output provenance.

## 5. Verify the accelerated v13 implementation

Locate the existing accelerated nonisothermal v13 implementation in the original project.

Identify the exact revision and acceleration mechanisms.

Verify its physical consistency against the accepted nonisothermal v13 baseline.

Compare:

- Water and salt inventories.
- Temperature and pressure.
- F36/W3 concentration profiles.
- Interface and bottom fluxes.
- Evaporation.
- Solid precipitation.
- Energy and mass conservation.

Document any differences caused by acceleration.

Do not substitute an unverified optimization branch or assume that multithreading automatically accelerates a serial DuMuX solver.

Freeze the verified baseline before launching the campaign.

## 6. Two parallel numerical research tracks

We will conduct two separate but coordinated campaigns.

### Track A — 2D mechanism investigation (high priority)

Develop a relatively inexpensive 2D heterogeneous F36/W3 model using the same verified nonisothermal physics.

Use a 50 mm wide and 40 mm high domain, divided vertically into coarse and fine materials.

A conventional 2D approximation is acceptable for the first mechanism study.

Do not spend unnecessary development effort reproducing the complete 3D cylindrical geometry or implementing a sophisticated 2.5D approximation before the initial tests.

Maintain physically consistent volume/flux normalization and clearly document the geometry assumptions.

**The purpose of 2D is to investigate whether changing the bottom boundary causes progressive, depth-wide salt accumulation in F36.**

We do not expect 2D to quantitatively reproduce the complete 3D finger morphology, instability onset, or experimental concentration magnitude.

However, we should examine whether the modified 2D model reproduces the experimentally observed qualitative behavior:

- F36 concentration increases over time.
- Upper, middle and lower F36 regions all become enriched.
- The vertical mean profile remains relatively uniform.
- The enrichment is supported by genuine salt accumulation and redistribution.
- Bottom supply remains physically plausible.

Run complete 174 h simulations when numerical validation permits.

### Track B — Full 3D investigation

Retain the original cylindrical geometry and verified nonisothermal v13 physics.

Continue the corresponding bottom-boundary cases using independent 3D simulations.

Use the 3D results to verify the physical effects of filter resistance, lateral redistribution, and central-inlet geometry.

Existing accepted 3D simulations remain the baseline and must not be replaced.

2D and 3D cases may be developed and run concurrently, subject to resource availability.

## 7. Bottom-boundary case matrix

### Group B — Equivalent porous-filter resistance

Use the existing distributed-reservoir boundary, adding a physically dimensioned common filter resistance.

Define a reference hydraulic resistance based on the initial F36 bottom half-cell:

`R_ref = mu_ref * d_ref / (K_F36 * kr_ref)`

Use the following exploratory cases:

| Case | Filter resistance |
|---|---|
| B0 | 0 |
| B1 | 0.1 × R_ref |
| B2 | 1 × R_ref |
| B3 | 10 × R_ref |

Use the same physical `Rf` for both F36 and W3 in each case. Do not scale the filter resistance independently by material.

Report `Rf` in Pa·s/m and its assumptions.

These are numerical sensitivity cases, not calibrated properties of the P3 filter.

Use the same input definitions in both dimensions whenever physically meaningful.

### Group G — Explicit filter and central-inlet geometry

Implement a 4.5 mm porous filter between the sand and the reservoir.

The porous filter must extend across the whole sample bottom.

The central inlet connects to the lower side of this filter, not directly to the sand.

Create three exploratory inlet-size cases:

| Case | Hypothetical 3D inlet diameter |
|---|---|
| G1 | 2 mm |
| G2 | 5 mm |
| G3 | 10 mm |

These are not confirmed experimental dimensions.

In 2D, the central inlet is represented by a slit. Select and document an appropriate hydraulic or conductance-based mapping. Do not claim direct geometric equivalence to a 3D circular inlet.

Use the same specified filter properties across G1–G3 to isolate inlet-size effects.

Include filter water/salt/energy storage and conservative interface coupling.

Avoid double-counting the filter resistance.

If the detailed plenum geometry is unavailable, use a clearly labeled simplified inlet/filter representation.

## 8. Primary evaluation criteria: F36 depth-wide enrichment

This section defines the most important scientific outputs.

### 8.1 Mean F36 concentration

Calculate the mean concentration in the 3–37 mm depth interval as a function of time.

We want to determine whether the modified bottom boundary produces sustained late-time concentration growth rather than the plateau predicted by B0.

### 8.2 Depth-resolved concentration evolution

Calculate mean concentrations in:

- Upper F36: 3–12 mm below the surface.
- Middle F36: 12–28 mm below the surface.
- Lower F36: 28–37 mm below the surface.

Compare the complete temporal evolution.

A successful mechanism should promote enrichment in all three regions, not just near the bottom or surface.

### 8.3 Vertical concentration distribution

For each case, calculate:

- Mean concentration.
- Standard deviation across depth.
- Vertical concentration gradient.
- Depth-resolved changes relative to the case's initial state and the baseline.

Use the experimental Figure 4.7d pattern as the physical reference.

Do not artificially force the profiles to be uniform.

### 8.4 Coarse-sand salt inventory

Compute dissolved, solid, and total NaCl inventories in F36.

Check whether increasing concentration represents greater salt retention rather than reduced liquid volume.

Report liquid saturation and pore-water storage.

### 8.5 Transport mechanisms

Quantify:

- Gross bottom water inflow/outflow.
- Gross bottom salt inflow/outflow.
- Outgoing bottom liquid concentration.
- Net F36 bottom salt supply.
- F36→W3 advective salt transfer.
- W3→F36 diffusive salt transfer.
- Net lateral salt transport.
- Downward and upward liquid velocities.
- Density/concentration anomalies.

Explain changes in F36 enrichment using quantitative conservation budgets.

### 8.6 Other required observables

Check W3 concentration, evaporation, energy balance, precipitation, and mass conservation.

Improvement in F36 must not be achieved through unrealistic suppression of water supply, excessive drying, or numerical artifacts.

## 9. Execution on sal using multiple cores

First inspect the actual `sal` resources:

- CPU architecture and core count.
- Available memory.
- Current workload.
- Scheduler availability and usage policies.
- Disk and scratch capacity.
- Solver MPI/OpenMP support.
- Observed runtime and peak memory of a representative case.

Use independent case-level parallelism as the default unless effective solver-level parallelism is verified.

Run multiple 2D cases concurrently when possible.

Keep the already authorized 3D work running independently.

Do not oversubscribe CPU cores or memory, and do not interrupt unrelated jobs.

Each case must have separate:

- Input directory.
- Execution directory.
- Output directory.
- Logs.
- Run status.
- Executable hash and parameter manifest.

### Execution sequence

1. Verify accelerated v13.
2. Build and validate 2D B0 and 3D baseline compatibility.
3. Start validated 2D B1–B3 cases concurrently.
4. Start validated 3D B-group cases using available resources.
5. Develop G1–G3 geometry in parallel with B-group execution.
6. Test the G-group hydrostatics, face geometry, mass/energy conservation and inlet flow distribution.
7. Queue validated G-group simulations.
8. Run complete 174 h cases where computationally feasible and permitted by available resources.

Do not treat a saved-state flux replay as a valid dynamic restart. Use a separately verified restart method if needed.

The campaign should proceed through actual authorized execution, rather than stop after writing a simulation plan.

## 10. Numerical validation

For every case:

- Verify hydrostatic equilibrium and initial saturation.
- Verify bottom and interface flux signs.
- Verify total water, salt and energy conservation.
- Verify filter and sand storage accounting.
- Check that the modified boundary does not introduce spurious pressure discontinuities or unphysical states.
- Check short-time numerical behavior before full runs.
- Perform targeted time-step and spatial-resolution comparisons before attributing small changes to physics.

Preserve solver failures and their diagnostic logs.

Do not silently change numerical tolerances or physical parameters to improve convergence.

## 11. Comparison and scientific conclusions

Prepare consistent plots for:

1. Experimental F36 concentration evolution.
2. 2D F36 mean concentration histories for B0–B3 and G1–G3.
3. 2D depth-resolved F36 concentration profiles.
4. F36 salt inventory histories.
5. Bottom gross inflow/outflow.
6. F36→W3 net salt transfer.
7. 3D concentration histories and profiles for available cases.
8. Evaporation and conservation.
9. Per-case computational runtime and memory.

Compare each 2D modified case against 2D B0, and each 3D modified case against the accepted corresponding 3D baseline.

Do not require absolute 2D–3D agreement.

The central questions are:

**Q1:** Can the modified bottom boundary transform F36 concentration evolution from a late-time plateau into progressive enrichment?

**Q2:** Does enrichment extend throughout the coarse-sand depth, rather than remain confined near the bottom?

**Q3:** Is the improvement caused by reduced loss of concentrated liquid, altered bottom replenishment, reduced lateral transfer to W3, or a combination?

**Q4:** Does the modification maintain physically credible evaporation and water/salt conservation?

**Q5:** Are the mechanisms identified in 2D also present in the corresponding 3D simulations?

A case should not be declared physically successful merely because its final F36 concentration is closer to the MRI measurement. Temporal behavior, spatial distribution, salt retention and coupled water flow must support the explanation.

## 12. Deliverables

Create:

`model_revisions/20261103_v13_bottom_boundary_campaign/`

with:

- `BASELINE_VERIFICATION.md`
- `MODEL_2D_IMPLEMENTATION.md`
- `BOUNDARY_IMPLEMENTATION.md`
- `CASE_MATRIX.csv`
- `RESOURCE_PLAN.md`
- `RUN_STATUS.csv`
- `2D_F36_CONCENTRATION_ANALYSIS.md`
- `BOTTOM_FLUX_COMPARISON.md`
- `2D_3D_COMPARISON.md`
- `FINAL_CAMPAIGN_ASSESSMENT.md`

Include figures, source files, input files, lightweight numerical results, solver logs, execution metadata and reproducible postprocessing scripts.

Maintain an independent research branch and preserve all accepted original results.

Report which cases actually started, completed or failed.

## 13. Final priority

The scientific priority is **the progressive enrichment of the entire F36 coarse-sand domain observed experimentally**, not isolated accumulation at the bottom.

The 2D campaign is a fast mechanism investigation. The 3D campaign provides the final physically representative assessment.

Investigate filter resistance and inlet geometry without assuming in advance that either must improve the model.

Use the simulations to test the hypotheses, quantify the mechanisms, and identify which bottom-boundary representations are justified by the experimental evidence.