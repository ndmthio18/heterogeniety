# Face-resolved W3 dry-crust evaporation screening

Task 8 / Task 3 completed 2026-11-05. This is a read-only, one-way screening of accepted `Greal-81` and `Greal-75` states. It is not a coupled DuMuX prediction. No accepted file, constitutive law, temperature, water activity, concentration, pressure, salt inventory or F36 flux was changed.

## Evidence and face correspondence

The accepted full `film_faces.csv`, budgets and seven selected native fields were SHA256-checked before extraction. The selected snapshots are 72, 84, 96, 108, 120, 144 and 174 h. [`scripts/extract_task8_inputs.py`](scripts/extract_task8_inputs.py) creates a compact analysis input while retaining full-file and selected-VTK hashes; [`scripts/screen_local_crust_resistance.py`](scripts/screen_local_crust_resistance.py) performs the mapping and screening.

The DuMuX top-face integration point is not generally the vertex-average centre stored for plotting in Task 2: their maximum separation is 0.344 mm. Consequently, no nearest-centre identity was assumed. Each integration point was required to lie inside exactly one actual VTK top polygon with matching area.

- Each case and time has exactly 384 W3 matches, 384 unique cell IDs and 384 unique integration points.
- There are no unmatched or duplicated faces.
- The mapped W3 area is `9.801714032956e-4 m²`; the largest area discrepancy against `film_faces.csv` is `8.67e-19 m²`.
- Face-integrated W3, F36 and total water fluxes reproduce `budget.csv` and `film_budget.csv`; the largest absolute discrepancy is `2.22e-16 g h−1`.
- The full mapping, input hashes and per-time ledger comparisons are recorded in [`results/W3_local_resistance_QA.json`](results/W3_local_resistance_QA.json).

These gates passed before resistance was evaluated.

## Conditional models

Only Task 2 solid with `precipitateVolumeFraction^NaCl > 1e−12` enters the resistance screen. Subthreshold numerical dust remains in the accepted inventory but produces exactly `beta=1`. For each detected face,

`h_i = alpha M_i / [2165 (1−0.43) A_i]`

and the dry/disconnected limiting factor is

`beta_i = 1 / [1 + (h_i/delta_air)/(Dcrust/Dair)]`.

The air films are the accepted `8.100162 mm` for Greal-81 and `7.5 mm` for Greal-75. External fractions `alpha=0.25, 0.5, 1.0` and diffusivity ratios `0.05, 0.08, 0.10, 0.23` are sensitivity scenarios, not fitted material properties. Task 6 showed that the published Nachshon et al. Table 2 coefficients and a direct recomputation from its displayed columns disagree substantially; the four ratios therefore cannot be treated as validated G-real bounds.

Three instantaneous models use the same detectable crust mass assumption:

- **A — original:** accepted local G-real flux, no added resistance;
- **B — uniform:** that mass is distributed over the complete W3 area;
- **C — local:** Task 2 mass remains on its matched bearing faces; uncovered faces retain `beta=1`.

Totals are obtained by integrating corrected local flux over actual face areas. No arithmetic mean of `beta` is used.

For within-face coverage `f`, the same local mass occupies covered area `f A_i`, so covered thickness is `h_i/f` and the parallel face factor is `(1−f)+f/[1+(h_i/f)/(delta_air r)]`. Sensitivities use `f=0.25, 0.5, 0.75, 1`; their mass reconstruction closes to `1.97e−16` relative error.

## Instantaneous evaporation results

### Terminal alpha=1, complete coverage of each detected face

| Case | Dcrust/Dair | Original W3 (g h−1) | Uniform W3 (g h−1) | Local W3 (g h−1) | Uniform reduction | Local reduction |
|---|---:|---:|---:|---:|---:|---:|
| Greal-81 | 0.05 | 0.131263 | 0.079328 | 0.099534 | 39.57% | 24.17% |
| Greal-81 | 0.08 | 0.131263 | 0.093149 | 0.105678 | 29.04% | 19.49% |
| Greal-81 | 0.10 | 0.131263 | 0.098892 | 0.108554 | 24.66% | 17.30% |
| Greal-81 | 0.23 | 0.131263 | 0.114909 | 0.118037 | 12.46% | 10.08% |
| Greal-75 | 0.05 | 0.140434 | 0.068799 | 0.097210 | 51.01% | 30.78% |
| Greal-75 | 0.08 | 0.140434 | 0.085072 | 0.104272 | 39.42% | 25.75% |
| Greal-75 | 0.10 | 0.140434 | 0.092353 | 0.107749 | 34.24% | 23.27% |
| Greal-75 | 0.23 | 0.140434 | 0.114513 | 0.120122 | 18.46% | 14.46% |

Uniform redistribution is more suppressive than local redistribution in every tested terminal scenario. It places resistance over the whole W3 surface, including uncovered faces that continue to evaporate in the local model. Hence a uniform equivalent thickness conserves salt mass but systematically overstates this particular dry-resistance screening relative to the reconstructed footprint.

For `alpha=1` and `Dcrust/Dair=0.08`, Greal-81 local resistance lowers W3 from `0.131263` to `0.105678 g h−1` (19.49%). F36 remains `0.149663 g h−1`, so the total sample rate changes from `0.280926` to `0.255342 g h−1` (9.11%). The corresponding uniform total is `0.242812 g h−1` (13.57% reduction). Greal-75 local and uniform total reductions are 12.03% and 18.42%, respectively.

At the same Greal-81 ratio of 0.08, local W3 reductions for `alpha=0.25, 0.5, 1` are `7.83%, 12.98%, 19.49%`; the uniform values are `9.28%, 16.98%, 29.04%`. These ranges demonstrate parameter sensitivity rather than parameter identification.

### Within-face coverage

At Greal-81 174 h, `alpha=1` and ratio 0.08, using the same local mass:

| Covered fraction of a bearing face | Local W3 reduction |
|---:|---:|
| 0.25 | 8.11% |
| 0.50 | 13.17% |
| 0.75 | 16.77% |
| 1.00 | 19.49% |

Smaller covered area creates a thicker covered patch but leaves more parallel exposed area. It therefore weakens the face-integrated resistance in this model. This sensitivity is not evidence that real crystal coverage equals one of these fractions.

## Spatial relationship and geometric confounding

At 174 h the numerical bearing areas are 48.61% (Greal-81) and 54.21% (Greal-75), while those faces carry 47.29% and 52.90% of the original W3 evaporation. Thus bearing faces do not preferentially contain a larger share of baseline evaporation than their area.

Across all W3 faces, terminal salt loading is negatively associated with simultaneous original flux (Spearman `rho=−0.663/−0.674` for Greal-81/75), positively associated with concentration (`0.757/0.764`), negatively associated with water activity (`−0.789/−0.823`), and strongly associated with interface and wall distances. These whole-surface values partly encode the spatial split between zero-loading and bearing regions.

Within detected faces only, loading and simultaneous flux instead have positive Spearman coefficients `0.734/0.751`. After rank-residual control for distance to the outer wall and F36/W3 interface, the coefficients fall to `0.196/0.176`. The sign change between all-face and detected-face analyses, followed by strong attenuation under geometric controls, shows that a single unqualified salt–flux correlation would be misleading.

The terminal maximum-loading face is not the face of maximum 72 h evaporation. Its 72 h flux lies only at the 1.56th percentile in Greal-81 and 17.19th percentile in Greal-75; terminal loading versus 72 h flux has Spearman `rho=−0.813/−0.843`. Therefore the accepted fields do **not** support the statement that the largest later salt loading occurs at the location of highest initial evaporation. This remains descriptive: geometry, concentration, activity, temperature and transport share common causes, and no causal mechanism is identified by these correlations.

## Validation and evidence boundary

All prescribed numerical gates passed:

- zero salt and `alpha=0` recover the original flux exactly;
- a `1e−18 m` height differs from `beta=1` by at most `1.55e−15`;
- increasing thickness never increases `beta`;
- all tested `beta` values lie in `[0.23218, 1]`;
- subthreshold and uncovered faces have exactly `beta=1`;
- F36 changes by exactly zero;
- uniform and local models use the same detectable salt mass for each `alpha`;
- original water/salt/energy budgets remain untouched.

The screen represents a dry or disconnected crust placed in series with the accepted air film. It does not represent a wet, hydraulically connected crust, external crystal area enlargement, heat redistribution, changing water activity, feedback on precipitation, or a new reservoir-loss prediction. The fixed baseline state is deliberately held unchanged.

Only seven matched snapshots were evaluated. Cumulative effects must not be obtained by assigning the 174 h map backward or silently interpolating masks. A defensible cumulative calculation would first require denser matched salt/face-flux fields, unchanged face correspondence, explicit treatment of appearance/disappearance between snapshots, and a validated temporal integration rule; a coupled prediction would additionally require conservative external-solid, heat and hydraulic feedback.

## Deliverables

- [`results/W3_face_evaporation_corrections.csv`](results/W3_face_evaporation_corrections.csv): 64,512 face/scenario rows for full bearing-face coverage.
- [`results/W3_uniform_vs_local_resistance.csv`](results/W3_uniform_vs_local_resistance.csv): 672 integrated A/B/C and within-face-coverage scenarios.
- [`results/W3_evaporation_weighted_coverage.csv`](results/W3_evaporation_weighted_coverage.csv): geometric and evaporation-weighted support histories.
- [`results/W3_spatial_correlations.csv`](results/W3_spatial_correlations.csv): all-face, detected-face and geometry-controlled descriptive correlations.
- [`results/W3_local_resistance_QA.json`](results/W3_local_resistance_QA.json): hashes, mapping, ledgers, validation gates and figure hashes.
- Figures `Figure_T8_1`–`Figure_T8_5` in PNG and vector PDF: local beta, original/corrected flux, uniform/local rates, correlation and snapshot evolution.

All PNGs are opaque RGB at nominal 300 dpi; PDFs use embedded TrueType fonts. The five figure sheets were visually inspected at delivered size. They are provisional scientific-review figures, not a claim of compliance with a specified journal.

Task 3 stops here. No Task 4 work was started.
