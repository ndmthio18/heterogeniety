# G-real evaporation comparison

Status: **pending complete 174 h primary cases**.

The comparison will use the original measured `time_h`, `mass_g` and `solution_loss_since_1h_g` columns in `inputs/experiment.csv`. Columns containing a previous model are provenance only and will not be treated as experiment.

Required metrics are full-window cumulative-loss RMSE, duration-weighted interval-rate RMSE, early/middle/late residuals and final 174 h error. Film selection will not use final loss alone. Greal-75 is not a validated full-window optimum until it completes and passes budgets.
