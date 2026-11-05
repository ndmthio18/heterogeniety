# W3 near-surface solid-salt reconstruction

Task 7 / Task 2 only, completed 2026-11-05. This is a read-only reconstruction of accepted `Greal-81` and `Greal-75` fields. No DuMuX run, physics change, resistance calculation, parameter fit or Task 3 implementation was performed.

## Evidence and reconstruction

The script [`scripts/reconstruct_w3_surface.py`](scripts/reconstruct_w3_surface.py) resolves the accepted PVD times at 60, 72, 84, 96, 108, 120, 144 and 174 h after the 2 h pre-equilibration. Before parsing, every selected VTK is checked against its previously recorded SHA256. The analysis then:

1. identifies each cell that has vertices at the actual sand top, `y=0.04 m`;
2. assigns W3 by the accepted material split, cell-centre `x>0.025 m`;
3. finds the unique three- or four-vertex top polygon for every top cell;
4. calculates its projected polygon area and the convex 3D cell volume;
5. calculates solid moles as `cell volume × precipitateVolumeFraction^NaCl × (2165/0.0584428) mol m−3`;
6. converts moles to NaCl mass with the same accepted `0.0584428 kg mol−1` convention; and
7. computes the hypothetical external height `h=M/[2165(1−0.43)A]` without changing the numerical field.

There are 384 W3 top cells and 384 unique mapped boundary faces. They include VTK hexahedra and wedges. Face areas range from `2.1271e−7` to `4.8923e−6 m²` (108 distinct values) and cell volumes from `1.4188e−11` to `3.2632e−10 m³`; treating the mesh as uniform would therefore be incorrect. The reconstructed discrete W3 area is `9.801714032956e−4 m²`, 0.1606% smaller than the analytical half circle.

The primary numerical detection rule is solid volume fraction `>1e−12`. Sensitivity rules `1e−15`, `1e−9` and `1e−6` give exactly the same bearing-cell counts and areas at every selected time. Raw subthreshold values remain in conservation totals; they are represented as no detectable local crust in coverage and thickness distributions.

## Conservation

For every case and selected time, the surface-cell molar sum was compared independently with the W3 top-1-mm row of `depth_profiles_compact.csv` and W3 `fine_solid_mol` in `mineral_budget.csv`. At 174 h it was also compared with the previous `inventory_summary.json`. No renormalization was applied.

- Acceptance tolerance: `max(5e−13 mol, 5e−10 × |reference|)`.
- Largest observed absolute difference: `6.33e−17 mol`.
- Largest observed relative difference: `1.15e−14`.
- All comparisons passed. Full per-time evidence and VTK hashes are in [`results/W3_spatial_mass_balance.json`](results/W3_spatial_mass_balance.json).

At 174 h, Greal-81 reconstructs `0.005487798553277463 mol` or `0.3207223 g`; the top-profile/mineral reference differs by `−1.73e−18 mol`. The slight mass difference from the earlier `0.320707 g` report is only the disclosed molar-mass convention (`58.4428` versus `58.44 g mol−1`), not a different inventory.

## Spatial results

### Greal-81 evolution

| Time (h) | Detectable W3 area (%) | Solid mass (g) | Mean height (mm) | P95 (mm) | Maximum (mm) |
|---:|---:|---:|---:|---:|---:|
| 60 | 0.000 | numerical dust only | 0 | 0 | 0 |
| 72 | 0.998 | 0.000000702 | 0.000000581 | 0 | 0.000059 |
| 84 | 16.580 | 0.004764 | 0.003939 | 0.034904 | 0.048818 |
| 96 | 25.738 | 0.020010 | 0.016543 | 0.109728 | 0.130760 |
| 108 | 32.552 | 0.044893 | 0.037115 | 0.204047 | 0.230951 |
| 120 | 35.677 | 0.078476 | 0.064879 | 0.312333 | 0.344534 |
| 144 | 42.708 | 0.168713 | 0.139481 | 0.560688 | 0.602510 |
| 174 | 48.611 | 0.320722 | 0.265152 | 0.917341 | 0.970143 |

The numerical support begins at the outer W3 circumference and expands inward as an annular band. It does not become spatially uniform. At 174 h only 120/384 top cells, representing 48.61% of the actual area, exceed the threshold. The area-weighted median height is therefore exactly zero, while P90, P95 and the maximum are 0.852, 0.917 and 0.970 mm.

The highest-loaded 10% of W3 area contains 34.72% of detectable solid mass; the highest-loaded 25% contains 76.18%; all detectable mass lies within 50% of total area. Thus deposition is strongly concentrated, but the highest 10% alone does not contain most of the salt. A quarter of the total surface does.

The area-weighted mean of 0.265152 mm agrees with the earlier approximately 0.265 mm uniform-equivalent estimate by construction of the same total inventory. It is 0.166% above the earlier 0.264713 mm calculation because this task uses the actual discrete surface area and accepted molar mass. That agreement says nothing about local geometry: P95 is 3.46 times and the maximum 3.66 times the mean, while more than half the area has no detectable solid.

For an externally assigned mass fraction `alpha`, every hypothetical height scales linearly. At 174 h, alpha `0.25/0.5/1.0` gives mean heights `0.0663/0.1326/0.2652 mm`, P95 `0.2293/0.4587/0.9173 mm`, and maxima `0.2425/0.4851/0.9701 mm`. These are transparent scenarios, not fits.

### Greal-75 comparison at 174 h

Greal-75 has `0.472296 g` in 138 cells covering 54.21% of W3. Its hypothetical mean, median, P95 and maximum heights are `0.3905`, `0.0356`, `1.1896` and `1.2401 mm`. Its highest-loaded 10% and 25% of area contain 30.62% and 69.57% of solid mass. It therefore carries more salt over a somewhat broader numerical support than Greal-81, while still remaining strongly nonuniform.

## Scientific answers and limits

1. **Uniformity:** The accepted numerical precipitation is localized in a peripheral annular band, not uniform over W3.
2. **Expansion:** Detectable numerical support expands monotonically from 1.00% at 72 h to 48.61% at 174 h in Greal-81.
3. **Dominant cells:** A small 10% area is important but not dominant (34.72% mass); the top quarter holds most mass (76.18%).
4. **Local versus uniform height:** The uniform estimate is only the area-weighted mean. Zero median and a 0.970 mm maximum reveal much larger local contrast.
5. **Uniform-crust error:** A uniform crust substantially misrepresents the model-derived footprint and local height distribution, even though it conserves total mass.
6. **Unknown physical geometry:** The solver represents equilibrium solid inventory inside top cells. It does not resolve external crystal shape, surface coverage, wetness, contact, nucleation delay, crawling, redistribution outside a cell footprint or salt lost/retained outside the MRI-visible solution. Numerical positive-support area is not observed external crust coverage.

No conclusion about evaporation suppression or enhancement follows from this reconstruction. The fixed-porosity/fixed-permeability production model also permits an equivalent solid volume fraction above geometrical pore capacity; local heights here are inventory reassignment diagnostics rather than validation of crystal morphology.

## Figures and data

- [`results/W3_surface_solid_maps.csv`](results/W3_surface_solid_maps.csv): 6,144 face-time rows with cell centres, geometry, actual area/volume, raw solid field, moles, mass loading and alpha-scaled heights.
- [`results/W3_surface_coverage_history.csv`](results/W3_surface_coverage_history.csv): four detection thresholds.
- [`results/W3_local_thickness_statistics.csv`](results/W3_local_thickness_statistics.csv): area-weighted height and ranked-area mass statistics.
- [`figures/Figure_T1a_Greal81_solid_loading_maps.png`](figures/Figure_T1a_Greal81_solid_loading_maps.png) and [`Figure_T1b`](figures/Figure_T1b_Greal81_hypothetical_height_maps.png): actual cylindrical grid, common logarithmic scales, gray subthreshold regions, no smoothing or interpolation.
- [`figures/Figure_T2_mass_concentration.png`](figures/Figure_T2_mass_concentration.png), [`Figure_T3_thickness_distributions.png`](figures/Figure_T3_thickness_distributions.png), [`Figure_T4_coverage_thresholds.png`](figures/Figure_T4_coverage_thresholds.png), and [`Figure_T5_Greal75_vs_81_174h.png`](figures/Figure_T5_Greal75_vs_81_174h.png).

All figures also have vector PDFs. The 12 figure files match [`results/W3_figure_manifest.json`](results/W3_figure_manifest.json); PNGs are explicit opaque RGB at nominal 300 dpi and representative PDF font resources are embedded. Visual inspection covered both map sheets and all diagnostic figures. Layout is a provisional general scientific-review format; no journal-compliance claim is made.

This completes Task 2. Task 3 remains unstarted pending review.
