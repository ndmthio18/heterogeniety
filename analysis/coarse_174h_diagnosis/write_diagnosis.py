"""Assemble reports only after complete A-C numerical checks."""
from pathlib import Path
import json
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent;O=R/'results'
checks=json.loads((O/'flux_analysis_checks.json').read_text());assert checks['passed']
b=pd.read_csv(O/'bottom_interval_budgets.csv');ix=pd.read_csv(O/'interface_gross_intervals.csv');err=pd.read_csv(O/'interface_quadrature_checks.csv');v=pd.read_csv(O/'vertical_native_transport.csv')
allc=b[(b.side=='F36')&(b.start_h==0)&(b.end_h==174)].iloc[0];late=b[(b.side=='F36')&(b.start_h==120)&(b.end_h==174)].iloc[0];iall=ix[(ix.start_h==0)&(ix.end_h==174)].iloc[0]
g=lambda x:f'{x*58.44:.6f}'
def md(df):
 def fmt(x):return f'{x:.6g}' if isinstance(x,(float,np.floating)) else str(x)
 return '\n'.join(['| '+' | '.join(map(str,df.columns))+' |','| '+' | '.join(['---']*len(df.columns))+' |']+['| '+' | '.join(fmt(x) for x in row)+' |' for row in df.itertuples(index=False,name=None)])
table=b[(b.side=='F36')&~((b.start_h==0)&(b.end_h==174))&~((b.start_h==120)&(b.end_h==174))][['start_h','end_h','bottom_gross_in_salt_mol','bottom_gross_out_salt_mol','accepted_bottom_net_supply_mol','accepted_interface_net_out_mol','accepted_salt_increase_mol']].copy()
for c in table.columns[2:]:table[c]=table[c]*58.44
table.columns=['Start h','End h','Gross bottom in g','Gross bottom out g','Accepted net bottom in g','Accepted net interface out g','Retained change g']
(R/'BOTTOM_BOUNDARY_FLUX_AUDIT.md').write_text(f'''# Bottom-boundary flux audit

**The model does export concentrated liquid through parts of the coarse bottom while dilute reservoir solution enters elsewhere. Nevertheless, its coarse bottom remains a net salt supplier over120–174 h.** The late inventory decline occurs because interface export exceeds that reduced net supply. Whether this open recirculation is excessive relative to the actual filter/plenum requires a controlled physical boundary test.

## Method and signs

Read-only native FV replay of1044 saved states from1/6 to174 h reconstructs primary variables from Float64 VTUs and calls the unchanged v12 boundary and interior flux routines. Every state passes original water/salt/material inventory and net-flux comparisons; maximum scaled discrepancy is{checks['native_replay_scaled_max_error']:.3g}. The accepted binary hash remains6595025e48333062cfa05022d9f6d65670421d33f5fb6c92213c0a402a10b58e. See `REPLAY_LOG.md`, build manifests and `native_replay/full/replay_checks.csv`.

For each bottom face, pressure/gravity driving is p_cell−p_res_face+rho_face*g*(y_cell−y_face). Negative driving selects the1mol/L reservoir as concentration/viscosity donor; positive selects the local brine. The total resistance is R_filter+mu*distance/(K*kr), with R_filter=0 in v12. Thus zero filter resistance does **not** mean infinite conductance: half-cell hydraulic resistance remains. It omits the additional real filter/plenum resistance and storage. Neumann component flux is per area and is multiplied by face area/extrusion once. Boundary salt exchange here is advective; no independent diffusive reservoir exchange is added.

Positive bottom flux is out of the sample. Gross in =sum max(−face_flux,0), gross out=sum max(face_flux,0). They are not abs(net). Water is reported both as H2O-component molar flux and liquid-solution volumetric flux, avoiding confusion with total solution mass. Outgoing concentration is salt-out/liquid-volume-out; incoming donor concentration is1mol/L. Correct donor identity,768-face geometry and signed/gross fixtures pass.

## Coarse-sand integrated result

- Gross incoming NaCl: **{g(allc.bottom_gross_in_salt_mol)}g**; gross outgoing NaCl: **{g(allc.bottom_gross_out_salt_mol)}g** (10-minute trapezoid).
- Original accepted net bottom supply: **{g(allc.accepted_bottom_net_supply_mol)}g**.
- Original accepted net interface export: **{g(allc.accepted_interface_net_out_mol)}g**.
- Retained increase: **{g(allc.accepted_salt_increase_mol)}g**, including the recorded seed impulse of{allc.seed_mol:.3g}mol.
- Relative to gross incoming salt: bottom export{allc.gross_in_fraction_bottom_export:.2%}, net interface export{allc.gross_in_fraction_net_interface_export:.2%}, retention{allc.gross_in_fraction_retained:.2%}. These are throughput accounting ratios, **not tracer fractions or unique molecular origins**; simultaneous recirculation can count the same physical salt more than once.
- Net interface export is{allc.net_supply_fraction_interface_export:.2%} of net bottom supply. Gross outflow is hidden by a net-only ledger.
- Integrated outgoing coarse liquid has salt/volume mean concentration{allc.outflow_weighted_C_mol_L:.4f}mol/L. At174 h outgoing concentration is1.46247mol/L, incoming1mol/L; coarse liquid-volume inflow/outflow are0.843946/0.516757mL/h. Simultaneous opposing flows occur on{allc.simultaneous_in_out_fraction_saved_frames:.1%} of sampled evaporation frames (threshold1e-16m³/s).

{md(table)}

All table salt quantities are NaCl-equivalent grams. Gross columns use10min replay quadrature; net/interface/retained columns use the accepted-step ledger. Both sands, water and volume histories are in `bottom_interval_budgets.csv` and `native_replay/full/flux_history.csv`.

## 120–174 h and causality

Gross coarse bottom in/out are{g(late.bottom_gross_in_salt_mol)}/{g(late.bottom_gross_out_salt_mol)}g; accepted net supply is+{g(late.accepted_bottom_net_supply_mol)}g. Interface export is{g(late.accepted_interface_net_out_mol)}g and coarse inventory change is{g(late.accepted_salt_increase_mol)}g. Therefore “net bottom salt loss causes the decline” is false for this interval. The accurate mechanism is large opposing bottom exchange plus net lateral export exceeding net replenishment. Removing bottom outflow alone would be a counterfactual that also changes pressure, inflow and interface flow; its outcome cannot be inferred by simply adding exported salt to the retained inventory.

The native bottom maps show inward/outward spatial regions; the fluid-state/velocity diagnostics show dense-brine descent connected to the boundary. These establish model transport pathways. They do not establish the actual experimental return flow or prove R_filter=0 is the dominant physical error.

This interval-integrated statement does not imply positive net supply at every instant. The original accepted ledger has a brief F36 **net outward** episode from 131.0833 through 138.9167 h (threshold 1e-12 mol/s), integrating 0.000154198 mol, or 0.009011 g. W3 becomes net outward from 128.1667 h through the end. These episodes and their thresholds are preserved in `instantaneous_net_export_episodes.csv`. The transient coincides with changing recirculation organization; it does not reverse the positive integrated F36 bottom supply over 120–174 h.

## Closure and resolution

Accepted material interval closure max absolute residual is{checks['accepted_interval_max_closure_mol']:.3g}mol. The complete original water/dissolved/solid/material budgets passed independently; dissolved and solid exchange internally through the equilibrium constraint, so only their sum is conserved without reaction terms.

The saved interval is600s, whereas the accepted trajectory commonly uses300s backward-Euler integration. `quadrature_net_error_mol` exposes the difference between reconstructed gross in−out and accepted net supply. The zero-hour saved field follows the seed whereas its ledger precedes the seed; gross quadrature uses hydrostatic zero flux at0h and does not claim exact sub10min startup. Interface10/20/60min sensitivity is in `interface_quadrature_checks.csv`. This is a diagnostic temporal-resolution check, not a new solver grid/dt convergence test. Interpret small differences accordingly.

Over the full window, F36 gross in−out differs from the accepted net supply by −1.78339e-5 mol (−0.0663% of net supply); W3 differs by −3.32723e-7 mol (−0.0327%). Signed interface advection/diffusion quadrature differs by 0.0412%/0.0363%; the largest individual-interval signed-component discrepancy is 0.3463%. The absolute native replay discrepancies are much smaller: water inventory at most 1.12e-15 mol, salt inventory 1.05e-16 mol, and bottom salt flux 2.05e-16 mol/s. `replay_absolute_errors.csv` supplies exact maxima. This separates storage/flux reconstruction precision from time-integration approximation.

Figures: [histories](results/05_native_flux_histories.png), [native face maps](results/06_native_flux_maps.png).
''',encoding='utf-8')
gr=[]
for q,label in [('salt_adv_mol_s','advection'),('salt_diff_mol_s','diffusion')]:gr.append({'Mechanism':label,'F36→W3 g':iall[q+'_coarse_to_fine']*58.44,'W3→F36 g':iall[q+'_fine_to_coarse']*58.44})
(R/'INTERFACE_AND_CONVECTION_AUDIT.md').write_text(f'''# Interface transport and convection

## Native interface decomposition

960 material-interface faces are counted once from the coarse side; total area0.002m². Native advective and diffusive methods return area-integrated component fluxes. Mass-averaged diffusive flux is converted to molar component flux using the component molar mass. No additional face area is applied. Water advection/diffusion and liquid-volume flow are exported independently. Positive is F36→W3.

The0–174 h10min gross salt integrals are:

{md(pd.DataFrame(gr))}

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
''',encoding='utf-8')
(R/'PHASE_1_FINDINGS.md').write_text(f'''# Phase1 findings — review gate before new long simulations

A–C offline/source/native-flux audit is complete.1044 saved-state flux replays and seven spatial/horizontal-face checkpoints pass verification. Original v12 is unchanged; this is a diagnostic branch, not a calibrated replacement model.

The three strongest findings are:

1. **Retention is limited by transport through boundaries, not absence of convection.** F36 gross bottom salt in/out are{g(allc.bottom_gross_in_salt_mol)}/{g(allc.bottom_gross_out_salt_mol)}g. Net bottom supply1.573102g is offset by net interface output1.341698g, leaving0.231405g. From120–174 h bottom remains a net supplier(+0.194006g), while interface export0.300254g causes net inventory decline. Test measured filter/plenum resistance and connectivity, reporting both gross and net exchanges; do not assert bottom net loss.
2. **The MRI comparison has an unresolved observation/supply consistency issue.**84–96 h full-profile apparent inventory grows0.011879mol versus0.003356–0.003483mol in an explicit inflow-only supply scenario. Manual edits and the recorded84→96 gain/power settings do not explain the jump. Calibration/processing, saturation/visibility, clocks and additional salt reservoirs must be audited; this is not proof that the experiment is wrong.
3. **Temperature fixes much of evaporation, not F36 accumulation.** Independent v13 improves total-loss error+11.06%→+0.83%, while174 h coarse concentration remains~1.23mol/L versusMRI2.45. A lower evaporation error is not a salt-transport validation.

The most discriminating next tests are a measured-resistance whole-filter/plenum comparison, an isolated material-interface/relative-permeability test within audited hydraulic data, and completion of the exact MRI processing chain. Detailed hypotheses, parameter provenance, signatures and GO/NO-GO gates are in `SENSITIVITY_MATRIX.md`. No new long174 h sensitivity runs or physical refit were launched. The task requires review of these findings and the test matrix before such runs.
''',encoding='utf-8')
(R/'SENSITIVITY_MATRIX.md').write_text('''# Preregistered sensitivity matrix — no long sweep launched

This matrix follows verified A–C findings. The accepted RH0/293.15K/8.100162mm film, initialφ0.40/0.36, K7.819185772e-12/3.203409878e-14m²,30720cells,2hpre+174hevap and300s cap remain frozen. No experimental concentration is used to choose a parameter. The current work verifies diagnostic replay and reuses the independent thermal case; it does **not** present new dynamically evolved hydraulic sensitivities as completed results.

| Test | Hypothesis and single change | Independent physical basis / required input | Expected discriminating signature | Falsification / decision |
|---|---|---|---|---|
| D1: filter resistance | H1: omitted filter resistance permits excessive recirculation. Add one common Rf while keeping1M reservoir/level/film unchanged. | Chapter p.48 identifies4.5mm P3 filter plate. Obtain water/brine head–flow curve or measured permeability; Rf=mu L/Kf in Pa·s/m. No Kf is supplied by the chapter/workbook, so no numerical Rf is invented. | Reduced opposing bottom throughput and changed outgoing C; determine whether net retention increases after pressure and lateral flow respond. | H1 weakens if a measured-resistance case leaves gross exchange/retention unchanged beyond numerical uncertainty. NO-GO if improvement requires unexplained starvation or worsens evaporation/W3 beyond predeclared tolerances. |
| D2: actual connection | H1/H4: filter/plenum/ports differ from prescribed independent reservoir faces. Represent whole filter contact plus actual3D plenum/inlet ports. | Chapter fig4.1 shows whole-base filter and lower connections. Need port radii/positions, plenum height, mixing and filter properties. A schematic is not a dimensional inlet specification. | Spatial outflow patterns and cross-sand circulation change at fixed reservoir chemistry/head. | Distributed sand–filter contact may remain appropriate even with localized external ports. Reject a central aperture if it misrepresents the intervening filter. Geometry alone is not implicated if verified connectivity leaves exchange unchanged. |
| D3a: material K | H2/H4: measured permeability uncertainty changes lateral transfer. Vary **one material's K only**, keepφ,retention curve,film fixed. | Hydraulic workbook provides three samples. Reconcile rawcm/day versus roundedm/s/cached averages first; `hydraulic_source_replicates.csv` records small inconsistencies. Use corrected independent replicate range, not fitted concentration bounds. | Interface advection/diffusion, gross bottom export, horizontal heterogeneity and F36/W3 growth respond coherently. | If effects remain below checkpoint spatial/temporal sensitivity, deprioritize K uncertainty. Do not promote betterF36 with worseW3/evaporation as success. |
| D3b: hydraulic functions | H2/H3: relative permeability/retention changes replenishment partition. Change one independently fitted curve family per case, preserving measuredKs. | Audit triplicate moisture curves and fit uncertainty; don't freely vary entry pressure/lambda/residual saturation together. Near-saturated bulk means effects may localize near the surface. | Changes in local saturation, supply and lateral exchange should precede concentration response. | No material effect under supported curves weakens the hypothesis. Reject parameter combinations that cannot reproduce independent retention measurements. |
| D4a: buoyancy mechanism | H4: density-driven connection to outlets causes low retention. Introduce a separately tested buoyancy-anomaly switch, while retaining composition-dependent storage/activity/viscosity. | Mechanism control, not a physically realistic alternative experiment. Requires explicit source audit; do not clamp density globally because that changes storage/phase equilibrium. | Downward structures and correlated boundary export decrease; quantify what remains of lateral capillary flow. | H4 insufficient if suppressing buoyancy removes descent but not retention deficit; budgets and hydrostatic consistency mandatory. |
| D4b: thermal closure | H3/thermal: evaporation bias causes concentration bias. Already available independent v13 adds specified energy/film/heat boundaries, withδunchanged. | Completed v13 source/acceptance/archive; not a fitted new case. | Evaporation improves; assess both sands and salt budgets. | Existing evidence: loss error falls to+0.83%, F36 mean remains1.23M. Thermal explanation alone is insufficient. |
| Observation control | H5: signal-to-concentration mapping drives some apparent growth. Reprocess native scans with recorded scaling, exact masks, H correction and exposure log. | Author processing chain/reference information; preserve untouched original profile variant. | Quantifiable changes in84–96h inventory/growth and full profiles, including both materials. | If independent processing reproduces profiles/inventory under verified liquid volume and supply, observation explanation weakens and physical mismatch gains weight. |

## Minimum implementation and short-test sequence

The existing v12 already accepts R_filter; **no new physical law is needed for D1** once its measured value is known. Promote the present per-face diagnostics into an isolated candidate revision first. For D2, `CentralAperture` is intentionally rejected for the cylinder: do not toggle it or reuse a2D slit. Mesh/test the actual3D filter/plenum geometry, native face area and reservoir hydraulic head; preserve the zero-resistance/distributed limit. Do not add a new salt-crust model during this audit.

1. Source/units gate: audit all changed parameters, independent provenance and dimensioned resistance. Resolve inlet geometry and hydraulic workbook conversion before assigning physical values. Missing measurements are a **NO-GO for calibrated physical claims**, not permission to invent them.
2. Code gate: sign/donor tests, bidirectional equal-net fixture, native face geometry, duplicate-face exclusion, water/total-salt/material closure, closed reaction and zero-change regression. Current replay sign/geometry/closure tests pass; a future dynamic boundary modification must repeat solver-level gates.
3. Inexpensive dynamic gate: zero-flow hydrostatic equilibrium,2h pre-equilibration+10min evaporation on the original grid, and a short post-onset comparison only from a **verified restart reader** or a separately budgeted start-to-checkpoint run. Current replay is not a restart reader. Do not claim a short startup case diagnoses174h retention.
4. Resolution gate: at an appropriate common checkpoint, compare dt300/150s and one targeted spatial refinement of the modified boundary/interface. Require conservation below the existing1e-6 acceptance threshold; require effects to exceed the measured numerical sensitivity before mechanistic interpretation. No such new full dynamic convergence evidence exists yet.
5. Review gate: present Phase1 findings and this matrix before full174h trials. Choose the minimum informative pair, not a multidimensional RMSE search. Retain all failures and originals.

For each approved full test, judge F36 mean/profile/gradient, W3 profiles, weighed solution loss and interval rates, gross bottom outflow, signed/gross interface transfer, dissolved/solid/material inventories and conservation together. A physical explanation requires a consistent change across these observables and independently supported parameters; conservation alone or isolatedF36 improvement is insufficient.

No artificial mechanical dispersion, arbitrary molecular-diffusivity increase, clock shift, time-dependent film coefficient, per-sand fitted evaporation factor, or post24h concentration fit is introduced. Existing v13/v14/v15/v16 activities are not interrupted.
''',encoding='utf-8')
stats=pd.read_csv(O/'profile_statistics.csv');tab=stats[(stats.band=='3-37')&stats.quantity.isin(['MRI_archived','model_liquid_M'])].pivot(index=['time_h','side'],columns='quantity',values='mean').reset_index();tab.columns.name=None
(R/'FINAL_DIAGNOSIS.md').write_text(f'''# Final diagnosis — coarse-sand174 h discrepancy

**The accepted model contains strong coarse-sand convection but retains too little salt. Native fluxes reveal simultaneous dilute bottom replenishment and concentrated bottom return, together with substantial net transfer into fine sand. This establishes the model's transport mechanism; it does not yet prove which experimental boundary or MRI assumption is responsible.**

The L1 audit is complete for existing-data diagnosis (A–C), controlled test design(D), and independent late-time-physics assessment(E). No accepted simulation/archive was overwritten and no new174h physical sensitivity sweep was launched. Work is isolated on `research/coarse-174h-discrepancy-audit`; main is not merged or changed.

## Quantitative result

- F36 gross bottom incoming/outgoing salt: **{g(allc.bottom_gross_in_salt_mol)}/{g(allc.bottom_gross_out_salt_mol)}g** (native saved-state10min quadrature).
- Accepted F36 net bottom supply1.573102g; net F36→W3 transfer1.341698g; retained increase0.231405g. Interface output offsets85.29% of net supply.
- From120–174h, F36 inventory **falls0.106248g** although bottom still supplies net0.194006g; interface exports0.300254g. “Net bottom export” is not the correct explanation of this interval.
- At174h F36 mean is1.234188 versusMRI2.449689mol/L. Mean-level bias contributes98.66% of profile MSE; shapeRMSE is0.141576mol/L. W3 profileRMSE is0.205039mol/L, with a much larger earlier84h error0.732860.
- The model's flat late vertical profile coexists with horizontal concentration RMS0.18760mol/L and coarse/core maximum descent1.008e-6/4.508e-7m/s. Mixing and accumulation are different observables.
- MRI84–96h combined apparent inventory rises0.011879mol, versus0.003356–0.003483mol under an explicit inflow-only supply scenario. This flags unresolved observation/supply assumptions; it is **not** a demonstrated experimental mass violation.
- Independent thermal v13 improves total solution-loss error from+11.06% to+0.83% but leaves F36 mean1.230835mol/L. Temperature/evaporation correction alone does not solve coarse retention.

### Matched whole-half3–37mm means (mol/L)

{md(tab)}

The model correctly conserves the specified components, generates concentrated descending coarse flow, retains strong material contrast, and produces a fine-sand solid inventory under its equilibrium assumption. It fails to reproduce the amplitude and late growth of coarse concentration and overpredicts late evaporation in its isothermal form. Its fixed-hydraulics solid variable exceeds geometric capacity and cannot be interpreted as a validated pore-blockage/crust description. A small finalW3 error does not validate earlier W3 evolution.

## Ranked causes and what is established

1. **Highest-priority physical hypothesis:** excessive hydraulic communication through a zero-added-resistance reservoir boundary and/or incorrect filter/plenum organization, acting together with lateral export. Supported by native recirculation and the documented4.5mm filter; excess relative to the experiment remains untested.
2. **Coupled interface hypothesis:** advection from coarse to fine exceeds reverse diffusion and consumes most net supply. That transfer is quantitatively established; whether its magnitude is wrong requires independently supported material/interface sensitivity, not fitted dispersion.
3. **Observation hypothesis:** calibration/normalization, visibility/liquid-volume mapping and exposure timing may contribute to apparent late coarse growth. Recordedgain/power do not step84→96h and manual edits have little effect; do not label simultaneous signal increases an artifact. Exact source processing remains unresolved.
4. **Thermal limitation:** strongly supported as an evaporation issue, insufficient as the coarse-concentration explanation. Existingv13 supplies the independent negative test.
5. **Late solid/surface transport limitation:** physically plausible and structurally absent, but not separately identified by these data. No newcrust model or arbitrary fit is warranted by this audit alone.

## Minimum next work and GO/NO-GO

First obtain filter head–flow/permeability and actual lower connection dimensions, and the exactMRI processing/exposure chain. Keep the existing resistance parameter rather than add fitting freedom. Test a measured whole-filter resistance and physically correct3D connection only after sign/geometry/hydrostatic/conservation gates. Then test one independently constrained material/buoyancy mechanism at a time. See `SENSITIVITY_MATRIX.md` for preregistered signatures/falsification and checkpoint resolution gates.

**GO:** source-supported inputs, passed zero-change/short dynamic gates, closed water/total/material salt, resolved numerical sensitivity, and coherent improvement of evaporation plus both sands. **NO-GO:** fittingF36 alone, unknown geometry assigned an arbitrary aperture, unexplained starvation, changed equations/tolerances/time labels, or a purported improvement smaller than numerical uncertainty. Phase1 findings and this matrix are presented for review before any newlong174h tests.

## Evidence and reproducibility

- [Six-page figure collection](results/COARSE_174H_AUDIT_FIGURES.pdf)
- [MRI concentration audit](MRI_CONCENTRATION_AUDIT.md)
- [Bottom gross/net budget](BOTTOM_BOUNDARY_FLUX_AUDIT.md)
- [Interface and convection](INTERFACE_AND_CONVECTION_AUDIT.md)
- [Phase1 review](PHASE_1_FINDINGS.md)
- [Controlled test matrix](SENSITIVITY_MATRIX.md)
- [Late-time thermal/precipitation assessment](LATE_TIME_PHYSICS_ASSESSMENT.md)
- Figures01–06(PNG/PDF), full metric/flux CSVs, source hashes, compiler manifests and replay checks in this directory. `README.md` distinguishes portable arithmetic verification, full offline extraction and native-environment replay.

All1044 replay frames reach174h and pass original net/inventory comparisons. Maximum scaled replay difference{checks['native_replay_scaled_max_error']:.3g}; accepted interval material closure{checks['accepted_interval_max_closure_mol']:.3g}mol. Ten-minute gross quadrature is reconciled with the accepted-step net ledger and downsampled for sensitivity; it is not exact accepted-step gross integration. No newfull-window grid/dt convergence or physical validation is claimed. Nominal clock, whole-half slab and approximate MRI observation assumptions remain explicit. Experimental crystallization time is not inferred from MRI; weighing-only rate-slope evidence remains conditional.
''',encoding='utf-8')
print('Reports assembled after A-C checks')
