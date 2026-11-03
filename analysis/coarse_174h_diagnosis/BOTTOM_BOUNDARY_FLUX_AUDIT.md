# Bottom-boundary flux audit

**The model does export concentrated liquid through parts of the coarse bottom while dilute reservoir solution enters elsewhere. Nevertheless, its coarse bottom remains a net salt supplier over120–174 h.** The late inventory decline occurs because interface export exceeds that reduced net supply. Whether this open recirculation is excessive relative to the actual filter/plenum requires a controlled physical boundary test.

## Method and signs

Read-only native FV replay of1044 saved states from1/6 to174 h reconstructs primary variables from Float64 VTUs and calls the unchanged v12 boundary and interior flux routines. Every state passes original water/salt/material inventory and net-flux comparisons; maximum scaled discrepancy is4.67e-07. The accepted binary hash remains6595025e48333062cfa05022d9f6d65670421d33f5fb6c92213c0a402a10b58e. See `REPLAY_LOG.md`, build manifests and `native_replay/full/replay_checks.csv`.

For each bottom face, pressure/gravity driving is p_cell−p_res_face+rho_face*g*(y_cell−y_face). Negative driving selects the1mol/L reservoir as concentration/viscosity donor; positive selects the local brine. The total resistance is R_filter+mu*distance/(K*kr), with R_filter=0 in v12. Thus zero filter resistance does **not** mean infinite conductance: half-cell hydraulic resistance remains. It omits the additional real filter/plenum resistance and storage. Neumann component flux is per area and is multiplied by face area/extrusion once. Boundary salt exchange here is advective; no independent diffusive reservoir exchange is added.

Positive bottom flux is out of the sample. Gross in =sum max(−face_flux,0), gross out=sum max(face_flux,0). They are not abs(net). Water is reported both as H2O-component molar flux and liquid-solution volumetric flux, avoiding confusion with total solution mass. Outgoing concentration is salt-out/liquid-volume-out; incoming donor concentration is1mol/L. Correct donor identity,768-face geometry and signed/gross fixtures pass.

## Coarse-sand integrated result

- Gross incoming NaCl: **6.888979g**; gross outgoing NaCl: **5.316919g** (10-minute trapezoid).
- Original accepted net bottom supply: **1.573102g**.
- Original accepted net interface export: **1.341698g**.
- Retained increase: **0.231405g**, including the recorded seed impulse of9.09e-09mol.
- Relative to gross incoming salt: bottom export77.18%, net interface export19.48%, retention3.36%. These are throughput accounting ratios, **not tracer fractions or unique molecular origins**; simultaneous recirculation can count the same physical salt more than once.
- Net interface export is85.29% of net bottom supply. Gross outflow is hidden by a net-only ledger.
- Integrated outgoing coarse liquid has salt/volume mean concentration1.4565mol/L. At174 h outgoing concentration is1.46247mol/L, incoming1mol/L; coarse liquid-volume inflow/outflow are0.843946/0.516757mL/h. Simultaneous opposing flows occur on89.8% of sampled evaporation frames (threshold1e-16m³/s).

| Start h | End h | Gross bottom in g | Gross bottom out g | Accepted net bottom in g | Accepted net interface out g | Retained change g |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 24 | 0.484096 | 0.0326077 | 0.453014 | 0.257071 | 0.195943 |
| 24 | 60 | 1.24468 | 0.782303 | 0.462061 | 0.349027 | 0.113034 |
| 60 | 84 | 0.985491 | 0.796828 | 0.188583 | 0.180718 | 0.007865 |
| 84 | 96 | 0.499836 | 0.410323 | 0.0895312 | 0.0847207 | 0.0048105 |
| 96 | 120 | 0.999423 | 0.813498 | 0.185907 | 0.169907 | 0.0160004 |
| 120 | 144 | 1.18648 | 1.13268 | 0.0535867 | 0.148073 | -0.0944866 |
| 144 | 174 | 1.48898 | 1.34868 | 0.14042 | 0.152181 | -0.0117615 |

All table salt quantities are NaCl-equivalent grams. Gross columns use10min replay quadrature; net/interface/retained columns use the accepted-step ledger. Both sands, water and volume histories are in `bottom_interval_budgets.csv` and `native_replay/full/flux_history.csv`.

## 120–174 h and causality

Gross coarse bottom in/out are2.675455/2.481358g; accepted net supply is+0.194006g. Interface export is0.300254g and coarse inventory change is-0.106248g. Therefore “net bottom salt loss causes the decline” is false for this interval. The accurate mechanism is large opposing bottom exchange plus net lateral export exceeding net replenishment. Removing bottom outflow alone would be a counterfactual that also changes pressure, inflow and interface flow; its outcome cannot be inferred by simply adding exported salt to the retained inventory.

The native bottom maps show inward/outward spatial regions; the fluid-state/velocity diagnostics show dense-brine descent connected to the boundary. These establish model transport pathways. They do not establish the actual experimental return flow or prove R_filter=0 is the dominant physical error.

This interval-integrated statement does not imply positive net supply at every instant. The original accepted ledger has a brief F36 **net outward** episode from 131.0833 through 138.9167 h (threshold 1e-12 mol/s), integrating 0.000154198 mol, or 0.009011 g. W3 becomes net outward from 128.1667 h through the end. These episodes and their thresholds are preserved in `instantaneous_net_export_episodes.csv`. The transient coincides with changing recirculation organization; it does not reverse the positive integrated F36 bottom supply over 120–174 h.

## Closure and resolution

Accepted material interval closure max absolute residual is4.19e-14mol. The complete original water/dissolved/solid/material budgets passed independently; dissolved and solid exchange internally through the equilibrium constraint, so only their sum is conserved without reaction terms.

The saved interval is600s, whereas the accepted trajectory commonly uses300s backward-Euler integration. `quadrature_net_error_mol` exposes the difference between reconstructed gross in−out and accepted net supply. The zero-hour saved field follows the seed whereas its ledger precedes the seed; gross quadrature uses hydrostatic zero flux at0h and does not claim exact sub10min startup. Interface10/20/60min sensitivity is in `interface_quadrature_checks.csv`. This is a diagnostic temporal-resolution check, not a new solver grid/dt convergence test. Interpret small differences accordingly.

Over the full window, F36 gross in−out differs from the accepted net supply by −1.78339e-5 mol (−0.0663% of net supply); W3 differs by −3.32723e-7 mol (−0.0327%). Signed interface advection/diffusion quadrature differs by 0.0412%/0.0363%; the largest individual-interval signed-component discrepancy is 0.3463%. The absolute native replay discrepancies are much smaller: water inventory at most 1.12e-15 mol, salt inventory 1.05e-16 mol, and bottom salt flux 2.05e-16 mol/s. `replay_absolute_errors.csv` supplies exact maxima. This separates storage/flux reconstruction precision from time-integration approximation.

Figures: [histories](results/05_native_flux_histories.png), [native face maps](results/06_native_flux_maps.png).
