# Final diagnosis — coarse-sand174 h discrepancy

**The accepted model contains strong coarse-sand convection but retains too little salt. Native fluxes reveal simultaneous dilute bottom replenishment and concentrated bottom return, together with substantial net transfer into fine sand. This establishes the model's transport mechanism; it does not yet prove which experimental boundary or MRI assumption is responsible.**

The L1 audit is complete for existing-data diagnosis (A–C), controlled test design(D), and independent late-time-physics assessment(E). No accepted simulation/archive was overwritten and no new174h physical sensitivity sweep was launched. Work is isolated on `research/coarse-174h-discrepancy-audit`; main is not merged or changed.

## Quantitative result

- F36 gross bottom incoming/outgoing salt: **6.888979/5.316919g** (native saved-state10min quadrature).
- Accepted F36 net bottom supply1.573102g; net F36→W3 transfer1.341698g; retained increase0.231405g. Interface output offsets85.29% of net supply.
- From120–174h, F36 inventory **falls0.106248g** although bottom still supplies net0.194006g; interface exports0.300254g. “Net bottom export” is not the correct explanation of this interval.
- At174h F36 mean is1.234188 versusMRI2.449689mol/L. Mean-level bias contributes98.66% of profile MSE; shapeRMSE is0.141576mol/L. W3 profileRMSE is0.205039mol/L, with a much larger earlier84h error0.732860.
- The model's flat late vertical profile coexists with horizontal concentration RMS0.18760mol/L and coarse/core maximum descent1.008e-6/4.508e-7m/s. Mixing and accumulation are different observables.
- MRI84–96h combined apparent inventory rises0.011879mol, versus0.003356–0.003483mol under an explicit inflow-only supply scenario. This flags unresolved observation/supply assumptions; it is **not** a demonstrated experimental mass violation.
- Independent thermal v13 improves total solution-loss error from+11.06% to+0.83% but leaves F36 mean1.230835mol/L. Temperature/evaporation correction alone does not solve coarse retention.

### Matched whole-half3–37mm means (mol/L)

| time_h | side | MRI_archived | model_liquid_M |
| --- | --- | --- | --- |
| 0 | F36 | 1.0574 | 0.999999 |
| 0 | W3 | 1.08003 | 1 |
| 24 | F36 | 1.14904 | 1.19272 |
| 24 | W3 | 1.19086 | 1.24711 |
| 48 | F36 | 1.24378 | 1.29789 |
| 48 | W3 | 1.24332 | 1.55004 |
| 60 | F36 | 1.3017 | 1.32215 |
| 60 | W3 | 1.23986 | 1.68102 |
| 84 | F36 | 1.47769 | 1.32923 |
| 84 | W3 | 1.17697 | 1.87558 |
| 96 | F36 | 1.94003 | 1.33401 |
| 96 | W3 | 1.55125 | 1.94552 |
| 108 | F36 | 2.00241 | 1.34584 |
| 108 | W3 | 1.62355 | 2.00518 |
| 120 | F36 | 2.1715 | 1.35404 |
| 120 | W3 | 1.79584 | 2.05835 |
| 144 | F36 | 2.27927 | 1.24851 |
| 144 | W3 | 2.03691 | 2.11865 |
| 162 | F36 | 2.36868 | 1.23404 |
| 162 | W3 | 2.18713 | 2.13107 |
| 174 | F36 | 2.44969 | 1.23419 |
| 174 | W3 | 2.26077 | 2.14082 |

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

All1044 replay frames reach174h and pass original net/inventory comparisons. Maximum scaled replay difference4.67e-07; accepted interval material closure4.19e-14mol. Ten-minute gross quadrature is reconciled with the accepted-step net ledger and downsampled for sensitivity; it is not exact accepted-step gross integration. No newfull-window grid/dt convergence or physical validation is claimed. Nominal clock, whole-half slab and approximate MRI observation assumptions remain explicit. Experimental crystallization time is not inferred from MRI; weighing-only rate-slope evidence remains conditional.
