# CPU and memory evidence

Prior frozen-source benchmark: original-grid7800–9600s one-thread reference455.27s; selected cached4-thread/partial/AMG-ILU150.36s. Detailed raw numbers and limits are in provenance/OPTIMIZATION_RESULTS.md. This campaign uses one DuMuX thread per case because of current sal availability, not four advertised threads without allocation.

New sal original-grid Baseline_short completed0–7800s: wall26m37.21s, user1582.47s/system12.25s,99% CPU, maximumRSS310800KiB (~303.5MiB), exit0. This includes2hpre+10min evaporation on one thread. Evidence results/baseline_resource_usage.txt. It does not estimate full174h cost; later nonlinear behavior and shared-node contention can differ. G memory remains to be measured by its short gates.
