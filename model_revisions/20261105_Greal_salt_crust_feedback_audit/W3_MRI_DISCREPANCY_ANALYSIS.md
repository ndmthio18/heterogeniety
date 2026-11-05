# MRI discrepancy: completed first quantitative comparison

The supplied unchanged MRI table has 440 observations per sand, at 11 nominal acquisition times. All 1,760 case/material observation pairs matched accepted model times and 1 mm depth bins exactly. No temporal or spatial interpolation was used. Both archived and recalibrated concentrations are preserved in `MRI_matched_pairs.csv`. MRI coverage is limited to the archived supplied table; it must not be presented as every acquisition in the thesis.

For Greal-81, W3 3–37 mm and recalibrated MRI:

| Window (h) | RMSE (M) | Bias, model minus MRI (M) |
|---|---:|---:|
| 0–60 | 0.3480 | 0.1546 |
| (60,84] | 0.7311 | 0.7010 |
| (84,96] | 0.4578 | 0.4334 |
| (96,108] | 0.4707 | 0.4570 |
| (108,144] | 0.3467 | 0.3283 |
| (144,174] | 0.2717 | 0.2326 |

Pre-model-precipitation RMSE is 0.3480 M; post-model-precipitation RMSE is 0.4398 M. These unequal windows have different observation counts and are not causal treatment groups. Nonzero error before model precipitation rules out crust feedback as a complete explanation of the discrepancy. The late improvement in residuals also rules out a simple claim that continuously growing solid inventory necessarily causes continuously growing concentration error.

The estimators give equal weight to each measured depth-bin pair. Source inspection of campaign_diagnostics.hh establishes that C_volume_mean_M uses overlap-weighted bulk cell volume, not liquid volume. A spatial average of MRI bins is not a liquid-volume-weighted experiment inventory. The CSV records interval differences in model concentration, MRI concentration and residual; these are finite differences between observations, not inferred continuous derivatives. This corrects the preliminary metadata wording without changing the numerical comparisons.

The 84–96 h change and archived-versus-recalibrated results require interpretation alongside original MRI calibration evidence. No statistical significance or measurement confidence interval is inferred without measurement-error estimates. Model precipitation time is not an observed nucleation time.

At 24/60 h W3 top-3-mm recalibrated biases already reach +0.699/+1.188 M; core biases are +0.036/+0.397 M. Thus substantial deterministic disagreement precedes detectable solid. Top-bin model mean growth slows from 0.02175 M/h over 48–60 h to 0.01647 over 60–84 h and 0.00985 over 84–96 h. MRI growth over those intervals is 0.01202, 0.02647 and 0.05953 M/h. These unequal finite intervals straddle onset and cannot establish a discontinuity at 71.92 h or isolate the precipitation sink from transport. The large MRI increase during 84–96 h contributes strongly to the falling residual.
