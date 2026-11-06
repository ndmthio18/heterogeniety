# v11 verification design — pre-registered (Opus B)

Registered 2026-10-30 19:11 UTC, before any v11 variant result existed. Changes after this point are appended as dated amendments with reasons, not edits.

## Scope

Numerical robustness of the paired connection effect E_1(t) = S_surface,W3(C1,B1,t) − S_surface,W3(C0,B1,t), where S_surface is the W3 (fine, x>25 mm) 0–3 mm NaCl-equivalent inventory in g, plus coarse-side, deep and whole-domain quantities. Grid, time step and perturbation checks; parameter checks only within traceable property intervals. This does not validate the model against experiment.

Causal switches (connected/disconnected interface; B=1/0) come only from the immutable A snapshot (`HANDOFF_READY.json`). B does not write its own implementation. Before A hands off, the frozen v08 binary is used only for engineering tests (runner regression, new-mesh geometry/hydrostatic pre-period, timing, memory). Those are labelled `RT_*` and never counted as effect checks.

## Meshes (generator `tools/make_mesh.py`, audit in `inputs/mesh/*_geometry.json`)

| level | nr/nt/nz | cells | top polygon area (m²) | flux area correction πR²/A | top layer (mm) | layers in 0–3 mm |
|---|---|---:|---:|---:|---:|---:|
| coarse | 8/48/27 | 10368 | 0.0019578928833 | 1.0028615075117908 | 0.101 | 12 |
| medium | 12/64/40 | 30720 | 0.0019603428066 | 1.0016081890839748 | 0.067 | 18 |
| fine | 18/96/60 | 103680 | 0.0019620938769 | 1.0007143040431583 | 0.044 | 26 |

- Same topology as the v06/v08 generator; vertical levels follow one geometric mapping (q40=0.9 for 40 layers, q=0.9^(40/nz)). Medium reuses the frozen v08 `cylinder.msh` byte-for-byte (SHA256 fc30b952…); the regenerated 12/64/40 mesh has identical connectivity and node differences ≤5.0e-8 m (y only; v05 rounding), confirming the generator.
- Refinement ratios: medium→fine 1.5 in r, θ and z; coarse→medium 1.5 (r, z) but 4/3 (θ). The family is not exactly uniformly refined. Richardson/GCI only if three-level behaviour is monotone and the observed order is plausible; otherwise none.
- Checks: material contact area 2RH=0.002 m² exactly, coarse volume fraction 0.5, circumcentre inside every cross-section, TPFA orthogonality (also checked by the solver's own `geometry_audit.json` at run start). The polygon volume differs from the nominal cylinder by 0.29/0.16/0.04 %; inventories are reported as computed (not volume-rescaled); this geometric approximation is part of the discretisation difference.
- Film thickness delta=0.008100162249880822 m is frozen. Only the polygon→circle flux-area correction changes per mesh (independent geometric quantity, not a weighing normalisation).
- Perturbation: same six physical-space Fourier modes, phases from RandomSeed, evaluated at cell DOF positions, normalised to volume-weighted RMS sigma on each mesh, then total-salt-corrected. Per mesh the seed partition impulses (`seed_event.json`) and the t=0 layer-anomaly RMS are recorded.

## Cases (each a C1/C0 pair at B=1, full 2 h + 24 h; only the listed keys differ from A's C1B1/C0B1 inputs)

| id | mesh | max dt | seed | sigma | priority |
|---|---|---:|---:|---:|---:|
| (A) C1B1/C0B1 | medium | 300 | 1 | 1e-5 | reused baseline |
| G_coarse | coarse | 300 | 1 | 1e-5 | 1 |
| T150 | medium | 150 | 1 | 1e-5 | 2 |
| G_fine | fine | 300 | 1 | 1e-5 | 3 |
| S2, S3 | medium | 300 | 2, 3 | 1e-5 | 4 |
| A3e-6, A3e-5 | medium | 300 | 1 | 3e-6, 3e-5 | 5 |
| P1–P4 (parameters, below) | medium | 300 | 1 | 1e-5 | 6 |
| B0 extension: G_fine, T150 at B=0 | — | — | 1 | 1e-5 | 7, only if A shows E_1−E_0 is a key result |

Runs are strictly serial on CPU5 (one solver), each pair back-to-back. Wall limits 6 h (coarse/medium), 12 h (fine). A timed-out/failed run keeps its identity and is reported; it is not silently retried. Inputs are derived by `tools/make_inputs.py`, which aborts on any key outside the registered set and records the exact diff.

## Parameter intervals (from `F36 & W3 Sand Hydraulic Properties.xlsx`, DARUS-6478; dump `analysis/hydraulic_workbook_dump.txt`)

- Ks F36: 3 packings × 3 repeats, individual 7.3–7.9e-5 m/s, packing means 7.40/7.77/7.77e-5, mean 7.644e-5 (model K_coarse=7.819e-12 m² is this mean converted with mu=1.002e-3, rho=998, g=9.81).
- Ks W3: 3 packings, individual 3.0–3.2e-7 m/s (sheet averages use 2 repeats each), packing means 3.05/3.15/3.20e-7; mean 3.133e-7 (model 3.2034e-14 m²).
- Porosity F36: 0.3897–0.3989 (Table 2), 0.3970–0.3992 (oven drying); model uses 0.40, outside both measured ranges. W3: 0.3483–0.3632 and 0.3471–0.3637; model 0.36.
- No traceable interval: D0/tortuosity/D_eff, dispersion, Brooks–Corey parameters (only point fits; refitting replicate curves would itself be a fit), the MRI column's own packing. The replicate intervals refer to separate packed cylinders (5 cm × 8 cm) and are lower bounds on the uncertainty of the experiment column.
- Pre-registered parameter pairs (medium, seed 1, C1/C0 each), all permeabilities converted with the same workbook formula k=Ks·1.002e-3/(998·9.81):
  - P1 minimum contrast: Ks_F36=7.3e-5, Ks_W3=3.2e-7 m/s.
  - P2 maximum contrast: Ks_F36=7.9e-5, Ks_W3=3.0e-7 m/s.
  - P3/P4 porosity corners are registered as not run: the inherited input path has no porosity-only switch audited for consistency with initial salt mass/retention scaling, and the 72 h budget is spent first on the pre-specified 14 numerical runs. They remain an uncovered uncertainty.
- D_eff ±10 % screening (exploratory only, if time allows): via `Revision.SaltDiffusionScale` 0.9/1.1, short window; labelled exploratory, no confidence interval.

Even if P1/P2 are run, permeability is only one of several uncertain inputs; the result can at most show the effect is (not) robust to the measured Ks replicate spread, not that it exceeds parameter uncertainty in general.

## Metrics (tools/metrics.py; same code for every case)

- Clock: evaporation time; frames 0/2/4/8/12/24 h and full 10-min series.
- Inventories (g NaCl-eq.) per side: 0–2, 0–3 (primary), 3–10, 10–20, 20–40, 0–40 mm by exact vertical overlap; band mean solution concentration = band salt / band liquid volume. Whole-domain total.
- Ledger per accepted step: per-side ΔS = B (bottom, + into sample) + I (interface, + into side) + seed impulse; residual reported. Evaporated water per side, side water storage.
- Interface: cumulative advective/diffusive coarse→fine salt; depth-banded and gross forward/backward only if the A handoff provides them (otherwise reported as not available, not reconstructed from frames).
- Plume: max q_down, descending volume fraction at 0.5/1/2e-8 m/s (all and core), persistence onset (3 consecutive frames, t≥0.5 h), core layer-anomaly RMS, enriched depth (deepest 1-mm bin above t=0 side mean +0.02/+0.1 mol/L).
- Independent check: raw-field side salt integral vs solver ledger at every frame.

## Acceptance / inference (PLAN rules, unchanged)

- Per run: full 24 h, finite, no precipitation, all relative budget residuals <1e-6, field-ledger agreement, hashes.
- Working tolerances (medium→fine and dt 300→150): surface inventory change ≤2 %, cumulative interface exchange ≤5 %, plume inventory/transport ≤5 %, onset difference ≤10 min. Applied both to each case and to the paired effect E (absolute g and relative; relative not used when |E| is near zero).
- Envelope over grid/dt/seed/sigma = finite scenario range, not a confidence interval. If the numerical spread is comparable to E, or E changes sign or the range includes zero → unresolved.

## Amendment 1 — operational gate definitions (2026-10-30 19:16 UTC, before any variant result)

For a refined/reference pair of cases (medium→fine; dt 300→150), relative difference = |X_ref − X_test| / |X_ref| with X from the finer (or smaller-dt) case as reference, evaluated at 24 h and reported also at 4/8/12 h:
- surface: per side, change of the 0–3 mm inventory since t=0 (ΔS_surf), and the inventory itself; gate ≤2 % on ΔS_surf at 24 h.
- interface: cumulative net coarse→fine salt (adv+diff) at 24 h, connected cases only; ≤5 %.
- plume inventory/transport: per side change of the 10–40 mm inventory since t=0, and per-side ledger bottom-supply salt; ≤5 %. Core descending volume fraction (1e-8) at 24 h reported, gated at ≤5 % only where both values exceed 0.01 (otherwise absolute difference reported).
- onset: persistent-downflow onset at 1e-8 m/s (all and core, both sides); |difference| ≤ 10 min; one-sided absence is a failure.
- Paired effect E (W3 0–3 mm, and the same for the other inventories): absolute difference in g and relative difference when |E_ref| > 10× the larger per-case field/ledger discrepancy and > 1e-4 g; otherwise only absolute.

## Amendment 2 — conditional B0 extension activated (2026-10-31 ~00:55 UTC)

PLAN rule: add B=0 fine-grid and 150 s pairs if E_1−E_0 is a key result. From A's four medium runs (identity-verified, extracted with tools/metrics.py): W3 0–3 mm E_1(24 h)=+0.00431 g, E_0=+0.00833 g, E_1−E_0=−0.00401 g; F36 0–3 mm E_1−E_0=+0.00430 g; the interaction is of the same magnitude as E_1 itself and changes sign between 12 h and 24 h. B therefore appends G_fine_{C1,C0}B0 and T150_{C1,C0}B0 (4 runs) after the registered B1 and P1/P2 cases, using A's C1B0/C0B0 templates with only the registered keys changed. If A's report later concludes that the interaction is not a key result, the not-yet-started B0 cases are removed from the queue and this is recorded. No other design element changes.

Erratum to Amendment 2 (appended 2026-10-31 03:48 UTC): the amendment was written at 03:07:39 UTC (file modification time), not "~00:55 UTC" as typed in its heading; content unchanged. Resource note: with the batch started 2026-10-30 19:07 UTC, the remaining serial queue (fine pair ≈16 h, four medium pairs ≈28 h, B0 extension ≈23 h) is projected to end close to the 72 h cap (2026-11-02 19:07 UTC); cases not finished by then are reported as incomplete, not shortened.

## Clarification of the Amendment 2 timeline (appended 2026-10-31 15:50 UTC, from logs; earlier text left unchanged)

The heading time "~00:55 UTC" in Amendment 2 was an incorrect estimate typed at writing time; it is not a prior registration time. Verifiable sequence (UTC): A `C0B0_24h` run_manifest end_utc 03:01:01.93 (A's fourth and last 24 h run); B extraction of A_C0B0 (remote `analysis/A_C0B0_24h/summary.json` mtime) 03:04:58.88; local B0 inputs/specs `inputs/prod_causal_v10c/v11_{G_fine,T150}_{C1,C0}B0.*` mtime 03:07:40; Amendment 2 text written at 03:07:39 (see erratum); remote B0 specs 03:08:25 and remote `queue.json` 03:08:36.68. The E_1−E_0 figures quoted in Amendment 2 therefore come from A's four completed runs, which existed before the amendment. No v11 B0 run directory existed at that time (none exists at 15:50 UTC either), so no v11 B0 result informed the decision. The conditional rule (PLAN: B0 fine + 150 s pairs if E_1−E_0 is key) and the queue position (after the registered B1 and P1/P2 cases) are unchanged.

Correction (appended 2026-10-31T16:03:32+00:00, timestamp from system clock): the preceding "Clarification of the Amendment 2 timeline" was written at 2026-10-31T15:48:00+00:00 (DESIGN.md modification time before this correction), not at the hand-typed "15:50 UTC" in its heading and in DESIGN.registered.sha256; its content is unchanged. All timestamps appended from now on are generated from the system clock.
