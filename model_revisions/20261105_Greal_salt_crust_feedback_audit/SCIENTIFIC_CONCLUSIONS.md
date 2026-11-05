# Phase I scientific assessment

## Answers to the seven decision questions

1. Essentially all detectable simulated solid is in W3's top 1 mm; selected native fields narrow it to the topmost 0.0667 mm cells. The external fraction is unidentifiable: these are internal storage variables, not resolved efflorescence. An upper-bound external assignment is plausible for screening but not established.
2. Full-coverage equivalent thickness at 174 h is 0.264713 mm (Greal-81) and 0.389817 mm (Greal-75), with the stated density/porosity. Coverage, porosity, density and unknown external fraction matter more than the 1-versus-2-mm classification in these outputs.
3. Full-coverage fixed-state screening for Greal-81 gives terminal W3 suppression of 76.6%, 39.5%, 24.6%, 11.6%, 3.16% for diffusivity ratios 0.01, 0.05, 0.1, 0.25, 1. The corresponding integrated evaporated-water reductions are 5.711, 2.231, 1.287, 0.569, 0.151 g. Only the first ratio is a verified literature fitted value, from different conditions. These are not coupled predictions or reductions of reservoir solution mass.
4. A wet connected crust may sustain evaporation if hydraulic supply and heat supply suffice; enhancement additionally requires a more effective exposed interface. Porosity alone is insufficient. Ali's 1H evidence of moisture above W3 makes a fully dry universal crust assumption inappropriate. Quantitative wet-crust prediction is unidentifiable without contact, permeability, retention and heat-transfer data.
5. Greal-81 begins detectable precipitation near 71.92 h (73.58 h at 1e-6 mol). W3 errors already occur by 60 h. Core recalibrated-MRI RMSE rises from 0.348 M before precipitation to 0.440 M after, but subsequently decreases while solid continues to grow. Missing crust feedback could affect later evolution; it cannot explain all errors or be established as their cause.
6. Early concentration bias cannot be attributed to the modeled post-onset crust. Bottom supply, interface advection/diffusion, fluid properties and MRI calibration remain alternatives; these outputs cannot rank their true experimental errors. Whole-column weighing does not measure W3 evaporation or lateral flux separately. Calling either flux 'excessive' therefore requires an unavailable local experimental constraint.
7. A fully parameterized crust-feedback module is not yet justified as an explanation or calibration strategy. A conservative design and validation plan are ready, but mechanism selection and quantitative compatibility with total evaporation are unresolved. See GO_NO_GO.md.

## Synchronized transport evidence

Greal-81 0–174 h F36-to-W3 salt transfer: advective net +0.039709 mol, diffusive net -0.014874 mol, combined +0.024835 mol. Sum of the separately resolved advective/diffusive absolute face transfers is 0.063645 mol. This gross measure counts opposing mechanisms and directions; it is not net supply or the absolute net-face flux. W3 filter-to-sand net supply is +0.003111 mol (advection +0.004171, diffusion -0.001060). Together these close the W3 total-salt increase. Windowed integrals use actual accepted dt, not hourly trapezoids.

At 174 h Greal-81 W3/F36 water evaporation is 0.131263/0.149663 g/h. W3 mean top-face activity is 0.78361, mean C 4.90087 M, top-cell temperatures 18.3996–18.7644°C. Surface area weighting and bulk-volume profile weighting are distinct. Native top temperature extrema are sampled at saved times, not inferred from reference-temperature diagnostic vapor pressures.

The total 1–174 h reservoir solution loss is 52.405721 g versus 51.52 g (+1.719%) for Greal-81. Strong hypothetical resistance is therefore not automatically an improvement: the largest water-flux reduction is much larger than the 0.886 g reservoir-solution discrepancy, although the two masses are not directly subtractable. Future coupled tests must recompute reservoir, liquid storage and salt budgets. F36 flux and lateral transfer can respond through pressure, concentration and temperature; the fixed-state screening holds them constant and cannot predict compensation.

## Evidence boundary

No new grid/time-step convergence, nucleation-delay model, MRI voxel reprocessing or independent validation was performed. Nominal acquisition times and the documented finite acquisition window remain. Numerical closure establishes internal accounting, not the truth of transport physics or MRI calibration. The source-specific dimensional diffusivity band remains unverified; Figure 3 is labelled accordingly.
