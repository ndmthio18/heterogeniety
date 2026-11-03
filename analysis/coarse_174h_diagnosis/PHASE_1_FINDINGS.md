# Phase1 findings — review gate before new long simulations

A–C offline/source/native-flux audit is complete.1044 saved-state flux replays and seven spatial/horizontal-face checkpoints pass verification. Original v12 is unchanged; this is a diagnostic branch, not a calibrated replacement model.

The three strongest findings are:

1. **Retention is limited by transport through boundaries, not absence of convection.** F36 gross bottom salt in/out are6.888979/5.316919g. Net bottom supply1.573102g is offset by net interface output1.341698g, leaving0.231405g. From120–174 h bottom remains a net supplier(+0.194006g), while interface export0.300254g causes net inventory decline. Test measured filter/plenum resistance and connectivity, reporting both gross and net exchanges; do not assert bottom net loss.
2. **The MRI comparison has an unresolved observation/supply consistency issue.**84–96 h full-profile apparent inventory grows0.011879mol versus0.003356–0.003483mol in an explicit inflow-only supply scenario. Manual edits and the recorded84→96 gain/power settings do not explain the jump. Calibration/processing, saturation/visibility, clocks and additional salt reservoirs must be audited; this is not proof that the experiment is wrong.
3. **Temperature fixes much of evaporation, not F36 accumulation.** Independent v13 improves total-loss error+11.06%→+0.83%, while174 h coarse concentration remains~1.23mol/L versusMRI2.45. A lower evaporation error is not a salt-transport validation.

The most discriminating next tests are a measured-resistance whole-filter/plenum comparison, an isolated material-interface/relative-permeability test within audited hydraulic data, and completion of the exact MRI processing chain. Detailed hypotheses, parameter provenance, signatures and GO/NO-GO gates are in `SENSITIVITY_MATRIX.md`. No new long174 h sensitivity runs or physical refit were launched. The task requires review of these findings and the test matrix before such runs.
