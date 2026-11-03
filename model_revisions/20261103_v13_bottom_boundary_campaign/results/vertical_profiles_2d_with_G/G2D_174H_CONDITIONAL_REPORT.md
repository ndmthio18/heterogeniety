# Conditional 2D G1–G3, 174 h comparison

G1–G3 each reached 174 h and passed their per-case water, salt, energy,
physical-state and field/ledger numerical checks. Each PVD contains 1,057
frames and ends at 633,600 s (2 h pre-equilibration plus 174 h evaporation),
with no missing registered gzip field. The local verified backup index contains
1,057 gzip fields for each G case.

These are **conditional sensitivity results**, not grid-accepted predictions.
The original doubled-resolution G1 screen remains failed: its nonlinear
residual plateaued at 1.04–1.09e-10, slightly above the fixed 1e-10 criterion,
after 12 timestep halvings. The production completion does not repair or
override that evidence.

## Experiment-profile comparison

The PDF uses the same archived whole-half MRI profiles, nominal clock, depth
coordinate and common concentration axes as the prior 2D B comparison. No
profile is interpolated, smoothed or fitted.

At 174 h, the 3–37 mm RMSE values are:

| case | F36 RMSE (mol/L) | W3 RMSE (mol/L) |
| --- | ---: | ---: |
| B0 | 1.04825 | 0.13321 |
| B3 | 0.60747 | 0.26013 |
| G1 | 0.51813 | 0.26345 |
| G2 | 0.51796 | 0.26336 |
| G3 | 0.55622 | 0.24905 |

Thus, G1–G3 improve the late F36 profile relative to both B0 and B3, but they
degrade W3 relative to B0. The mechanism changes salt partitioning between the
two sands; it does not improve both halves simultaneously. G1 and G2 remain
nearly indistinguishable, and G3 differs only modestly.

At 24 h, all cases are close. At 60 h, G is slightly worse than B0 in both
halves. By 108–174 h, the F36 improvement becomes clear while the W3 penalty
persists. Therefore the scientifically defensible statement is a conditional
redistribution effect, not general experimental validation or identification
of a real port size.

MRI profiles use nominal acquisition times and do not determine crystallization
onset. The 2D slit mapping matches only the initial conductance of hypothetical
3D ports and does not reproduce 3D spreading or front/back-wall heat transfer.
