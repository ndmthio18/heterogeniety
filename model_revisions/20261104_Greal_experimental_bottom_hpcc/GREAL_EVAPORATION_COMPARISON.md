# G-real evaporation comparison

Status: **complete 174 h primary cases; scalar comparison passed QA**.

The comparison will use the original measured `time_h`, `mass_g` and `solution_loss_since_1h_g` columns in `inputs/experiment.csv`. Columns containing a previous model are provenance only and will not be treated as experiment.

Both cases reached 174 h. The comparison is restricted to measured points from
1 through 174 h; the 180 and 186 h measurements are not clamped to the model
endpoint.

| Case | 1--174 h loss (g) | Final error | Cumulative RMSE (g) | Duration-weighted rate RMSE (g h-1) |
|---|---:|---:|---:|---:|
| Greal-75 | 56.0068 | +4.4868 g (+8.709%) | 1.7812 | 0.03529 |
| Greal-81 | 52.4057 | +0.8857 g (+1.719%) | 0.6239 | 0.02476 |

Greal-75 retains its previously observed early-window advantage, but its rate
remains too high later and it overpredicts the complete cumulative loss.
Greal-81 is the better full-window member of this controlled pair by every
evaporation metric above. Nevertheless, the measured interval rate declines
more strongly than either model. Therefore the result selects Greal-81
relative to Greal-75; it does not independently validate the constant-film
boundary or identify actual humidity.
