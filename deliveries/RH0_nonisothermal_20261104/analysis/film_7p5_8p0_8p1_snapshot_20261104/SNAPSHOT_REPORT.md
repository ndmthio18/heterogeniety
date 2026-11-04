# 7.5/8.0/8.10 mm evaporation snapshot

The 7.5 and 8.0 mm simulations are partial (39.92 and 46.00 h); 8.10 mm is complete to 174 h. No partial trajectory is extrapolated.

The fair ranking uses the original experimental points common to every model, 1-36 h. By duration-weighted interval-rate RMSE, **7.5 mm (partial) is currently closest** (0.03538 g/h). See `metrics_common_1_36h.csv` for all cumulative and rate errors.

The 8.10 mm complete simulation predicts 51.94784 g solution loss over 1-174 h versus 51.52 g measured (+0.830%). That full-window result cannot yet be compared fairly with the incomplete 7.5/8.0 mm runs.

The figure uses measured points, unsmoothed model output, a common zero at 1 h, and a visible endpoint marker for partial simulations. Raw snapshots and SHA256 provenance are in `raw/` and `manifest.json`.
