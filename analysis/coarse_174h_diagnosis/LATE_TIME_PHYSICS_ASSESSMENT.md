# Late-time evaporation and precipitation: v12 versus independent v13

The available independent nonisothermal calculation substantially improves evaporation while leaving the late F36 concentration deficit essentially unchanged. This separates two problems that should not be fitted with one parameter.

| Metric | v12 isothermal | v13 nonisothermal |
|---|---:|---:|
| Film thickness / RH | 8.100162 mm / 0 | same, no refit |
| 1–174 h reservoir **solution** loss | 57.216967 g | 51.947836 g |
| Error against measured51.52 g | +11.0578% | +0.8304% |
| Duration-weighted interval-rate RMSE | 0.040368 g/h | 0.023923 g/h |
| First accepted equilibrium-solid event | 57.5833 h | 70.7500 h |
| Final solid NaCl equivalent | 0.373802 g | 0.226441 g |
| 174 h F36 mean, 3–37 mm | 1.234188 mol/L | 1.230835 mol/L |
| 174 h F36 profile RMSE | 1.223719 mol/L | 1.227029 mol/L |
| 174 h W3 profile RMSE | 0.205039 mol/L | 0.199613 mol/L |

v13 was already completed independently under separate user authorization. This audit launched no thermal simulation. `thermal_comparison.py` reads nine required archive members, verifies each against `final_174h_manifest.json`, and exports concentration/evaporation/partition comparisons. The complete v13 archive had already been verified as1146 members/1057 raw fields, SHA256 `716288ecba754a483d4faa3e34fbdb0a400cb38b416272b24f4b024cde3f7ec3`. The present audit verifies the used members, not a new full6.3GB archive re-audit. Original acceptance records pass water/salt/material budgets (maximum6.36e-13 relative), energy1.83e-10, and mineral complementarity1.84e-16. These are numerical checks, not physical validation.

## Why v12 increasingly overpredicts loss

The v12 error grows from −0.13% over1–24 h to +15.15% over60–174 h. Its boundary uses a fixed equivalent film thickness,293.15 K, unified solution water activity and no measured-total normalization. As surface concentration rises, water activity reduces vapor driving force; it is not a humidity-independent imposed flux. However, the fixed thermal state does not cool with evaporation, and the film does not acquire an independent evolving crust resistance or resolved exposed-surface geometry.

v13 solves energy and evaluates surface saturation pressure, film gas density and diffusivity with evolving temperature. Its174 h temperatures span18.3087–19.6756°C. Reduced vapor transport under these **specified thermal assumptions** is sufficient to bring total loss near the observation, but not to establish the actual heat-transfer coefficient. Top sensible heat conduction uses the same equivalent film thickness. Side/bottom heat supply uses a5mm plexiglass wall, conductivity0.184 W m⁻¹ K⁻¹, fixed20°C exterior, without external convection resistance. Reservoir inflow/outflow uses corresponding donor enthalpy. Crystallization heat and external efflorescent morphology are absent. Thus the paired run isolates this implementation's thermal closure, not temperature alone under a measured thermal boundary.

It would be incorrect to interpret the agreement as proof that a crust adds no resistance, or to lower gas diffusivity until F36 matches. The vapor-transfer coefficient, thermal supply and actual exposed salt surface remain potentially compensating physical uncertainties. Existing v15/v16 calibration/transport work is not imported as an accepted baseline here; its different calibration objectives/settings and ongoing activities remain separate.

## Evaporation partition and solid inventory

v12 cumulative F36 top-water share is53.1088%; at174 h the area-normalized fluxes are4.2298mm/day F36 and3.6121mm/day W3, so they are not equal. The instantaneous share evolves smoothly from approximately50% toward54%; v13 is similar. `thermal_inventory_partition.csv` gives checkpoints, and `04_thermal_and_evaporation` shows both histories. There is no independently measured per-half evaporation curve here; attributing this partition to the real experiment remains a model inference.

All final v12 solid inventory is in W3. With fixed φ/K, the equivalent solid-volume variable reaches10.9767 (v13 reaches8.2833), vastly exceeding geometric pore volume. This is a conserved inventory representation, not a physically admissible pore occupation or validated salt-crust morphology. Consequently these cases cannot predict pore blockage, crust thickness, nucleation delay, changing external surface area, or crust transport resistance. A macroscopic external-crust model would need additional conservation domains and independent parameters; none was added in this audit.

At liquid–solid equilibrium, saturation constrains dissolved concentration while solid inventory can continue growing. A water-activity-only film can therefore approach a persistent transport rate without any solid-dependent resistance. That structural assumption is a credible late-time limitation, but the existing thermal result shows that evaporation mismatch alone cannot identify crust resistance. F36 mean concentration remains about half the MRI value in both thermal closures. Missing heat transport is therefore not a sufficient explanation for the F36 retention discrepancy.

## Evidence boundaries and next observations

Only weighing-derived rates are used for experimental timing arguments. The prior40–60 h rate-slope candidate is conditional on fitting window/model choice and is not verified crystallization onset. The model's57.58/70.75 h equilibrium-solid events are not experimental nucleation times. Neither the MRI concentration series nor the chapter96–108 h window is used to assign onset in this audit.

Priority measurements are sample surface/internal temperatures and external heat-transfer conditions; exposed salt morphology/surface coverage versus time; and separated water/salt/filter inventories. A physically altered boundary should be judged jointly by evaporation, both-sand concentration, solid/dissolved inventories, gross exchange and conservation. Improving the total-loss curve alone does not validate the salt-redistribution mechanism.

Figure: [independent thermal comparison](results/04_thermal_and_evaporation.png). Numbers and provenance: `thermal_profile_metrics.csv`, `thermal_evaporation_intervals.csv`, `thermal_member_verification.json`, plus the unchanged v12/v13 reports and acceptance records.
