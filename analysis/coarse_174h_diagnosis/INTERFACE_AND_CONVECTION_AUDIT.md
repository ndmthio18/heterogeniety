# Interface transport and convection

## Native interface decomposition

960 material-interface faces are counted once from the coarse side; total area0.002m². Native advective and diffusive methods return area-integrated component fluxes. Mass-averaged diffusive flux is converted to molar component flux using the component molar mass. No additional face area is applied. Water advection/diffusion and liquid-volume flow are exported independently. Positive is F36→W3.

The0–174 h10min gross salt integrals are:

| Mechanism | F36→W3 g | W3→F36 g |
| --- | --- | --- |
| advection | 2.52223 | 0 |
| diffusion | 0.0798079 | 1.26095 |

The original accepted **signed** integrated advection/diffusion are+2.523265/−1.181567g; net+1.341698g. Gross directional values can be larger than signed values because simultaneous counterflow or sign changes cancel in the net. `interface_gross_intervals.csv` reports each requested interval and water/volume decomposition; `interface_quadrature_checks.csv` reconciles saved-state quadrature with accepted cumulative flux. Do not confuse diffusion returning salt toward F36 with absence of advective export toward W3.

## Density-driven redistribution

Native checkpoint fields were read at24,60,84,96,120,144,174 h. `convection_diagnostics.csv` gives both materials, whole-half and core regions, concentration/density layer anomalies, horizontal concentration RMS, upward/downward volume fractions, velocity extrema and concentration-anomaly/vertical-velocity correlation. The core excludes3mm adjacent to the interface, radii>20mm, and the upper/lower5mm. Velocity is the original interior-face least-squares reconstruction; these are simulated velocities, not MRI-derived experimental velocities.

At174 h F36 maximum downward velocity is1.00814e-6m/s over all coarse cells and4.50802e-7m/s in the core. Volume fractions descending faster than1e-8m/s are33.60%/25.72%. Whole-coarse layerwise concentration heterogeneity RMS is0.18760mol/L; the corresponding density anomaly RMS is7.21543kg/m³. Concentration anomaly and upward velocity correlation is−0.97342 (core−0.98679), consistent with concentrated dense liquid descending. This is a field association, not a separate gravity-off causality experiment.

Three actual horizontal native-face levels, at heights11.0026,19.0235,30.2801mm, are evaluated rather than fabricated10/20/30mm planes. At174 h net upward F36 advective salt transport is2.7604e-8,2.7407e-8,2.3662e-8mol/s respectively, despite concentrated descending streams. `vertical_native_transport.csv` separates gross up/down and net, and includes both sands. Bulk upward supply and concentrated downward recirculation coexist; net-upward transport does not rule out bottom export. These fluxes are native FV results, not products of averaged concentration and reconstructed velocity.

The central-band cell-centre maps (|z|<1.5mm) show wall-side and interface-adjacent descending structures at24–120 h. By174 h the sampled central band is dominated by the interface-adjacent concentrated descending region, while substantial lower-concentration upward regions remain elsewhere in the coarse half. Bottom/interface face maps and whole-volume diagnostics guard against interpreting one section as the entire3D flow.

## Why a flat vertical profile does not mean adequate accumulation

F36 model mean(3–37mm) changes from1.35404mol/L at120 h to1.24851 at144 h and1.23419 at174 h. Depth SD falls from0.08475 to0.01453/0.01586mol/L, while horizontal heterogeneity persists. Vertical averaging of heterogeneous recirculation can thus yield a flat mean profile. It is incorrect to equate this with full3D homogenization or successful salt retention.

At174 h mean bias=−1.21550mol/L, profile RMSE=1.22372mol/L and demeaned shape RMSE=0.14158mol/L. The exact decomposition RMSE²=bias²+shape_RMSE² assigns98.66% of squared error to the mean. W3 RMSE is0.20504mol/L, but its earlier84 h RMSE is0.73286mol/L; matching its final profile does not validate the evolution. All temporal growth, gradient and bandwise results are in the A tables.

120–174 h accepted F36 bottom net input0.194006g is smaller than net interface output0.300254g. The difference explains the0.106248g inventory decline through transport accounting, even though dense convection exists. This identifies the model's mechanism, not which experimental boundary or observation assumption is wrong. Spatial near-uniformity cannot compensate for an inadequate net salt budget.

## Ranked explanations, with evidential status

1. **Observed model mechanism: open bottom recirculation combined with net F36→W3 export limits F36 retention.** Strong native flux and closure evidence. Excessive experimental loss or excessive interface transport is still a hypothesis; independent return-flow/filter data are absent.
2. **Observed measurement-model inconsistency: late whole-depth MRI growth, especially84–96 h, is not explained by the simple inflow-only apparent-inventory scenario.** Strong source/budget evidence for an unresolved comparison problem. It does not prove an MRI artifact. Corrected-GV scaling, acquisition clocks, saturation/visibility and excluded reservoirs need resolution.
3. **Isothermal late evaporation bias is real but insufficient to explain coarse concentration.** Independently accepted v13 improves total loss yet leaves final F36 mean~1.23mol/L. Thermal closure is necessary to test; it does not remove the retention problem.
4. **Interface hydraulic organization/material uncertainty could change partition and circulation.** Plausible, untested. The final horizontal heterogeneity and cancellation of advection/diffusion make it worth testing; no fitted dispersion or arbitrary diffusivity increase is warranted.
5. **Fixed-hydraulics equivalent-solid storage is not a physical late crust model.** Structural limitation is demonstrated by super-geometric inventory values. Its causal effect on the F36 deficit cannot be quantified without a separately validated surface/filter/crust representation.

Figures: [internal fields](results/03_coarse_internal_fields.png), [native fluxes](results/05_native_flux_histories.png), [native maps](results/06_native_flux_maps.png). Numerical conservation is not physical validation; no new full-window grid/dt convergence was performed.
