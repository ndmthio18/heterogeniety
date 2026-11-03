# MRI concentration audit — archived experiment versus v12

The late F36 discrepancy is primarily a mean-level error, not failure to make a vertically uniform profile. At 174 h the model mean over 3–37 mm is 1.234188 mol/L and the archived MRI mean is 2.449689 mol/L. Mean bias accounts for 98.66% of profile mean-square error. This comparison alone cannot determine whether the missing retention is physical-model error or measurement-operator error.

## Reconstructed quantities and source chain

`analyze_archives.py` reproduces both materials at 0, 24, 48, 60, 84, 96, 108, 120, 144, 162 and 174 h. `results/profile_statistics.csv` gives mean, population depth SD, least-squares slope per mm, 3–12/12–28/28–37 mm bands, and changes from 0/60 h. `profile_growth_rates.csv` gives interval growth. Depth SD describes spatial variation; it is **not measurement uncertainty**. All bins are nominal 1 mm, whole material-half cross-sectional averages, following chapter pp.58–59; no unsupported central-ROI alternative is introduced.

Five quantities are kept separate:

1. Archived MRI concentration: cached workbook concentration, including author edits and alignment/partial-volume treatment.
2. Native reconstructed MRI: binary `2dseq` plus reconstruction metadata, before the archived ImageJ processing. These source files exist and are hash-identified. They are not the profile CSV's `raw_signal` column.
3. Workbook reconstruction-corrected GV: the former CSV `raw_signal`, originating under `Profiles_30.01.25!A3 = Reco Corrected GV`. Its ImageJ ROI/normalization lineage cannot be regenerated exactly from the workbook alone.
4. Recalibration: apply the recorded calibration inverse to the corrected GV, before concentration-cell edits. For F36, C=(GV−0.96)/(2.62×0.39). For W3, C=[2.6693−sqrt(7.1241−0.9032(GV−0.6991))]/(0.4516×0.35).
5. Model liquid molarity: xNaCl×liquid molar density/1000, averaged by native cell-volume overlap with each whole-half slab. This is not the salt inventory.

The chapter pp.49–50 records ~32 min sodium acquisitions, 1×1.375×1.375 mm voxels, whole-half profile targets, volume-concentration calibration, and a 1.5-pixel median filter. Native ImageJ masks/macros, exact boundary-voxel rules, and a complete per-scan processing chain were not found in the extracted archive (search `.roi`, `.ijm`, processed `.csv/.txt`; source workbook and raw scans are available). The chapter's visualization spike removal must not be assumed to be a documented quantitative-profile mask. This audit retains nominal-clock comparisons and instantaneous model profiles. It does not claim a complete voxel/PSF/32-minute forward model or shift scan times to improve fit.

## 84–96 h increase: evidence and limits

| Quantity | F36 | W3 |
|---|---:|---:|
| Archived concentration increase, mol/L | 0.462348 | 0.374279 |
| Before concentration edits, mol/L | 0.457015 | 0.374279 |
| Corrected-GV relative increase | 18.789% | 18.195% |

Manual concentration edits explain very little of this interval increase. Their complete locations and formulas are in `manual_and_alignment_changes.csv` and `workbook_cell_provenance.csv`. Some edits replace depth samples, and some superficial W3 cells add partial-volume corrections; the two processing routes must not be merged silently.

The 84 h E39 and 96 h E41 scans both have RG=64, reference power=5 W, the same recorded spatial resolution, matrix, 32-minute scan duration, repetition and echo settings. There is **no recorded receiver-gain or reference-power step between these two scans**. Their reconstruction slopes change from 631.212917 to 793.783043; `VisuCoreDataSlope` is the corresponding reciprocal. This scaling must be applied exactly when comparing binary data. Its change is not, by itself, proof of a signal artifact: it is an image reconstruction scale, not an independently measured physical signal increase.

There is a real earlier power transition. `2W_5W_Corr.` explicitly compares E31/E39, with mean packed-pixel ratio E70=1.460161. E31 is labelled in the main workbook as a 1.46 correction case. Most processed profiles are pasted numbers, so the exact application of this factor to every voxel/ROI cannot be verified from formulas. The factor is neither a demonstrated 84–96 h switch nor a justified correction to apply again to the final profiles.

Acquisition timestamps are available. E39→E41 spans 11.7512 wall-clock hours versus 12 nominal hours. This small interval difference does not explain a 31% concentration rise. There are larger accumulated timing discrepancies: the 174 h-labelled scan starts about 194.16 h after the first acquisition, and the 108→120 h labels span about 23.64 wall-clock hours. Pause/exposure logs are not provided, so elapsed acquisition time must not be substituted for evaporation exposure without confirmation. `scan_metadata.csv` preserves both clocks and source fields.

The workbook also contains hydrogen scans at 0/24/174 h and a filter-plate normalization, not an absence of water-content evidence. Its endpoint factor N215=1.292551 gives sample signal ratio Q55/Q54=1.08018 after the recorded correction. This does not establish 8% extra saturation; normalization, spatial alignment and relaxation remain relevant. It supplies no resolved saturation map at 84/96 h. The chapter says periodic H scans were used to check saturation, supporting a near-saturated scenario, but it does not supply the full time-resolved observation operator needed for an exact inventory audit.

Thus simultaneous signal increases are an **observation to audit**, not grounds to declare the experiment erroneous. Actual accumulation, calibration response, unresolved processing, timing and water-content response remain distinguishable hypotheses requiring source evidence.

## Apparent inventory and independent supply

For independently known liquid concentration and saturation, n=Σ C[ mol/L ] φ Sw V[ m³ ]×1000. Initial pore volume, current liquid volume and MRI observation volume must be distinguished. Here, the recorded calibration maps voxel signal to bulk sodium volume concentration and then divides by initial experimental porosity (F36 0.39; W3 0.35). Consequently, under that observation model, φ_initial C_archived V is the **apparent dissolved inventory**; multiplying it by an assumed Sw again double-counts saturation. Alternatively treating C_archived as true liquid concentration requires an independently justified Sw and a different interpretation of calibration. Both routes are documented; neither is promoted to measured total salt.

`MRI_apparent_inventory.csv` uses nominal radius 25 mm and height 40 mm, with full 0–40 mm and interior 3–37 mm separately. Model porosities 0.40/0.36 are not substituted into experimental inventories. The 0–40 mm profiles include uncertain top/bottom treatment; no external crystalline salt is inferred from sodium images. For W3's nonlinear response, inverse of averaged signal differs from average of local inverse: exact voxel data/processing are needed to remove this ambiguity.

Between 84 and 96 h, direct reservoir **solution** mass loss is 3.49 g. A 1 mol/L reservoir, inflow-only exchange and density scenarios 1.002–1.040 g/mL give 0.003483–0.003356 mol of supplied NaCl. The lower density is the workbook convention, the upper is an approximate saline-solution scenario; this is a sensitivity bracket, not a measured confidence interval.

| Observation volume / processing | Apparent increase (mol) | Ratio to inflow-only supply |
|---|---:|---:|
| 0–40 mm, archived | 0.011879 | 3.41–3.54 |
| 0–40 mm, before edits | 0.012375 | 3.55–3.69 |
| 3–37 mm, archived | 0.010391 | 2.98–3.10 |

Under the alternative *true-liquid-C* interpretation and uniform Sw, starting at Sw84=1 would require Sw96≈0.841–0.844 to reconcile the full-profile increase with this supply. That is a diagnostic threshold, not an inferred saturation field and not a permissible second saturation correction to bulk-calibrated data. There is no 84/96 h H-field evidence demonstrating this change. Physical bounds 0≤Sw≤1 alone are too broad to identify the inventory.

Redistribution **between** F36 and W3 cancels from the combined inventory; it cannot alone supply the summed increase. Movement from excluded end layers can affect the 3–37 mm inventory. Solid dissolution, filter/other stored brine, changes in visible sodium fraction, and differences in observed volume can affect apparent dissolved inventory. Reservoir loss is net solution loss, not a direct measure of gross NaCl inflow; concentration of returning brine and reservoir composition history are not measured here. Therefore the factor-of-three mismatch is a **conditional supply–observation inconsistency**, not a demonstrated mass-balance violation or proof that MRI is wrong.

## Approximate forward observation and priority checks

`model_observation_approximation.csv` applies the archived calibration to model φ Sw C before slab averaging, then divides the inverted mean signal by experimental φ. It includes the measured/model porosity distinction but not exact MRI voxelization, median filtering, relaxation or temporal averaging. At 174 h it changes F36 mean from 1.2342 to 1.2658 mol/L and RMSE from 1.2237 to 1.1923 mol/L; it does not remove the factor-of-two discrepancy. Model saturation is nearly unity, so simple model desaturation is not the explanation.

Required follow-up evidence is the saved ImageJ ROI/macro or exact export procedure; per-scan reconstruction and 2W/5W normalization chain; co-registered H/Na data around 84/96 h; exposure/pause logs; and reservoir/filter dissolved and solid salt accounting. No experimental values were adjusted in this audit.

Figures: [concentration/error](results/01_concentration_and_error.png), [signal/apparent inventory](results/02_signal_and_apparent_inventory.png). Source hashes: `results/source_manifest.json`; metadata/workbook CSVs retain cell and scan identifiers.
