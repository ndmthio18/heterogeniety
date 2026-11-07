# Exploratory 174 h completion

## Scope and status

The fully coupled vapor-resistance calculation completed 2 h pre-equilibration plus 174 h evaporation on Frodo with return code 0. It is a user-authorized exploratory calculation released before all preregistered Gates A–F were complete. It must not be presented as a fully verified or experimentally validated crust model.

The model uses the current equilibrium solid NaCl inventory in each atmospheric top cell as one conserved external inventory. That inventory determines a local equivalent porous-crust height and a current-Newton-state vapor-resistance correction. It is not duplicated as a second precipitation source. Additional crust thermal conduction was excluded; the original nonisothermal gas-side conduction remained active and the corrected vapor flux entered the existing vapor-enthalpy term once.

## Completed-run scalars

| Quantity | Exploratory coupled result |
|---|---:|
| Evaporation endpoint | 174 h |
| Wall time | 25,292 s (7.03 h) |
| Reservoir solution loss, 1–174 h | 51.5403455 g |
| Experimental reservoir solution loss | 51.52 g |
| Endpoint difference | +0.0203455 g (+0.03949%) |
| First accepted equilibrium solid | 71.9167 h |
| Final W3 external solid mass | 159.643 mg |
| Final maximum equivalent height | 0.390557 mm |
| Final detectable crust-bearing area | 542.413 mm2 |
| Final same-state W3 flux suppression | 13.8128% |
| Final temperature range | 18.4227–19.7573 degC |
| Maximum absolute water residual | 1.72e-13 mol |
| Maximum absolute salt residual | 2.01e-15 mol |
| Maximum absolute energy residual | 6.03e-6 J |
| Maximum deeper positive solid inventory | 8.14e-35 mol |
| Maximum complementarity residual | 1.83e-16 |

The 13.8128% value compares corrected and uncorrected W3 fluxes at the same final driving state. It is not the cumulative change in reservoir loss. The close cumulative endpoint is a fitted-model comparison and does not independently validate the dry-crust mechanism or its assumed diffusivity ratio.

## Time-resolved evidence

- At 75 h, only about 3.08 h of post-onset feedback had occurred. The coupled and baseline reservoir-loss curves were effectively coincident; the coupled 1–75 h loss was lower by 0.0449 mg.
- At 132 h, the cumulative error relative to experiment changed from -0.19389 g for Greal-81 to -0.43444 g for the coupled case, while the duration-weighted interval-rate RMSE improved from 0.024365 to 0.023502 g/h.
- Over post-onset MRI pairs at 84–120 h and 3–37 mm, F36 RMSE changed from 0.29214 to 0.29042 M, whereas W3 changed from 0.52639 to 0.53296 M. This is not a uniform concentration improvement.

These partial-window comparisons show that the coupled mechanism changes the trajectory, but a favorable final cumulative endpoint alone is insufficient evidence of improved time-resolved physics.

## Evidence retained in Git

- `source/`, `tests/` and `scripts/`: implementation and reproducible lightweight tests/analysis.
- `results/partial75/`: early post-onset comparison and compact source tables.
- `results/partial133/`: later partial comparison, metrics and figures.
- `results/w3_surface_animation_174h/`: selected-time native W3 face geometry, reconstructed inventory, QA and visualization products.

Raw full-field VTU/PVD output, solver executables and duplicate tar archives are intentionally excluded from Git.
