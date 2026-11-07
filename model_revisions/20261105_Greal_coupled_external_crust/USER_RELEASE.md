# User-directed exploratory 174 h release

The user explicitly instructed "直接放行" after being told that enabled integration, post-onset dynamics and mesh/timestep verification were incomplete. This authorizes an exploratory 174 h run without those prior gates. It does not establish numerical qualification or physical validation.

ExternalCrust.AllowUnqualifiedProduction=true lifts only the 96 h admission limit. Existing water/salt/energy, complementarity, fixed-hydraulics, negative-solid, external-inventory reconstruction and deeper-solid checks remain active. Original Greal81 parameters, 8.100162249880822 mm film thickness, ratio 0.08, crust porosity 0.43, fraction/coverage 1 and zero added crust thermal resistance remain unchanged.

The run starts from original initial conditions, for 2 h equilibration plus 174 h evaporation. Prior sources, builds, tests and accepted G-real outputs remain preserved. Results must be labelled exploratory until the outstanding verification is completed.

The independent Frodo run subsequently completed the 174 h target with return code 0. Completion did not change its exploratory qualification.
