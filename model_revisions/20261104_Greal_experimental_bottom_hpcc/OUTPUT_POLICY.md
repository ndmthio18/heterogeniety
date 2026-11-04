# Output policy

The numerical checkpoint grid remains 600 s and is not an output-control parameter. The currently admitted safe fallback is `Benchmark.VtkEvery=6`, producing approximately hourly full fields while retaining the initial and final states.

High-frequency compact accepted-step outputs retain water/salt/energy budgets, material inventories, evaporation, cumulative reservoir exchange, interface fluxes and 1 mm F36/W3 depth profiles. Concentrations include explicit liquid-volume weighting; dissolved, solid and total salt are stored separately. Detailed top-film face values use the registered diagnostic interval `Benchmark.FaceOutputInterval=3600 s`; this does not alter the time loop or integrated film history.

Full fields retain concentration, saturation, temperature, pressures, density, precipitated salt, material/filter identity and liquid velocity. Detailed face maps are not accepted as high-frequency production output unless their size and scientific use are justified.

The preferred 23-event selective schedule is not yet admitted for this explicit-filter executable. Hourly fallback is used until a G-real output-equivalence test demonstrates identical accepted states, budgets and compact profiles. Precision remains Float64.
