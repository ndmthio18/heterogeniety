# VERIFICATION_REPORT — v11 grid / time-step / perturbation / parameter checks of the connection effect (Opus B)

Generated 2026-11-01T03:28:07+00:00 by `tools/build_report.py` (model claude-opus-5-5). Protocol: `model_revision_plan/20261030_opus_campaign/PLAN.md`; pre-registration `DESIGN.md` (hash log `DESIGN.registered.sha256`).

**Report status: IN PROGRESS — not a final report; queued cases still running.** Completed new production runs: 14/22; failed/interrupted: 0 .

| run | state | wall (h) | accepted steps | max rel. residual |
|---|---|---:|---:|---:|
| v11_G_coarse_C1B1 | completed | 0.56 | 332 | 5.6e-13 |
| v11_G_coarse_C0B1 | completed | 0.61 | 332 | 1.0e-12 |
| v11_T150_C1B1 | completed | 3.45 | 629 | 3.4e-13 |
| v11_T150_C0B1 | completed | 2.61 | 629 | 5.3e-13 |
| v11_G_fine_C1B1 | completed | 5.58 | 332 | 1.7e-11 |
| v11_G_fine_C0B1 | completed | 5.52 | 332 | 1.7e-11 |
| v11_S2_C1B1 | completed | 1.77 | 332 | 5.9e-13 |
| v11_S2_C0B1 | completed | 1.80 | 332 | 3.8e-13 |
| v11_S3_C1B1 | completed | 1.90 | 332 | 4.1e-13 |
| v11_S3_C0B1 | completed | 1.15 | 332 | 6.3e-13 |
| v11_A3e-6_C1B1 | completed | 1.37 | 332 | 4.3e-13 |
| v11_A3e-6_C0B1 | completed | 1.21 | 332 | 2.2e-13 |
| v11_A3e-5_C1B1 | completed | 1.41 | 332 | 7.1e-13 |
| v11_A3e-5_C0B1 | completed | 1.59 | 332 | 6.9e-13 |
| v11_P1_C1B1 | running | 0.26 | – | – |
| v11_P1_C0B1 | queued | – | – | – |
| v11_P2_C1B1 | queued | – | – | – |
| v11_P2_C0B1 | queued | – | – | – |
| v11_G_fine_C1B0 | queued | – | – | – |
| v11_G_fine_C0B0 | queued | – | – | – |
| v11_T150_C1B0 | queued | – | – | – |
| v11_T150_C0B0 | queued | – | – | – |

Reused medium baselines (A, handoff `causal_v10c`, identity verified: binary cb57a841…, inputs per snapshot manifest, mesh fc30b952…): C1B1_24h, C0B1_24h, C1B0_24h, C0B0_24h; extracted with the same B extractor. C1B1_24h equals v08 Dry_trial02_r02 in every B frame metric (difference 0.0).

## 1. Summary (numbers from this batch; inference limits in §8)

- Primary effect E_1 = S_W3,0–3mm(C1,B1) − S_W3,0–3mm(C0,B1), medium/dt300/seed1/σ1e-5: +0.00031, +0.00083, +0.00229, +0.00422, +0.00431 g at 2/4/8/12/24 h (NaCl 58.443 g/mol; A uses 58.4428, ratio 1+3.422e-6).
- dt 300→150 s: E_1(24 h) +0.00432 g vs medium +0.00431 g (0.11 % relative to the finer reference).
- medium→fine grid: E_1(24 h) +0.00431 g vs medium +0.00431 g (0.06 % relative to the finer reference).
- coarse (info): E_1(24 h) +0.00443 g vs medium +0.00431 g (2.67 % relative to the medium reference).
- Perturbation phase/amplitude pairs available: S2: E_1(24 h) +0.00431 g, S3: E_1(24 h) +0.00431 g, A3e-6: E_1(24 h) +0.00431 g, A3e-5: E_1(24 h) +0.00431 g.
- Interaction E_1−E_0 (W3 0–3 mm, 24 h): MEDIUM: -0.00401 g.
- Finite scenario envelope of E_1(24 h) over the 8 available B1 pairs: +0.00431 … +0.00443 g; sign change: no. This is a range over registered numerical/parameter variants, not a confidence interval.
- Working tolerances not met medium→fine (kept as failures, no tolerance/physics change): see §4.1 table (F36 surface-change 2.28 %/2.37 %, F36 surface effect, F36 deep effect, connected F36 core descending volume fraction 47.8 %, W3 net vertical transport at 3 mm in C1).

## 2. Methods and provenance

### 2.1 Execution environment
- liqin, CPU5 only (`taskset -c 5`), `nice 10`, OMP/OpenBLAS/MKL/TBB threads 1, one solver at a time. Controller `remote/controller.py` (flock single instance) runs the ordered `queue.json` serially; `remote/run_case.py` runs one case: resource gates before launch (MemAvailable ≥8 GiB, scratch ≥8 GiB + expected size, home ≥2 GiB — waits, never fails, while short), wall limit (6 h coarse/medium, 12 h fine), peak RSS from `/proc/<pid>/status` VmHWM, closed VTU frames gzip-archived with raw-SHA256 = decompressed-SHA256 before the raw copy of that new frame is removed, `run_manifest.json` with binary/input/mesh hashes, acceptance validation.
- Remote tree `/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_verification_v11` (scripts, inputs, meshes, status, reduced analysis); raw runs `/tmp/zhixin_verification_v11_20261030/runs/<case>`.
- Python on liqin: `/home/zhixin/micromamba/envs/vasca311/bin/python3` (Python 3.11.13, NumPy 2.1.3, pandas 3.0.2). System Python was not used for analysis.
- No compilation was performed by B (the handoff binary is used as delivered and hash-verified), so the shared compile lock was never taken.

### 2.2 Pre-handoff engineering tests (frozen v08 binary c9145e42…, not effect checks)
| test | purpose | result |
|---|---|---|
| RT_medium_v08bin | runner/pipeline regression vs v08 Dry_trial02_r02 to 1 h evaporation | budget.csv rows bitwise identical (57 rows); raw VTU SHA256 identical at 0/2/3 h; 12.5 min wall; peak RSS 0.22 GiB |
| RT_coarse_v08bin | new-mesh solver geometry audit, 2 h zero-evaporation stationarity, timing | solver audit passed (contact 0.002 m², sin non-orth 4e-13); pre-period salt/water drift ≤2e-15 relative, S=1; 1 h film water 0.35305 g vs medium 0.35302 g; 4.0 min wall; 0.12 GiB |
| RT_fine_v08bin | same for fine mesh; memory/time projection | see §2.3 |

## 4. Results

### 4.1 Grid (B=1, connected/disconnected pairs; coarse 10368, medium 30720, fine 103680 cells)

| quantity (24 h, g) | coarse | medium | fine | medium→fine rel | three-level |
|---|---:|---:|---:|---:|---|
| E W3 0–3 mm | +0.00443 | +0.00431 | +0.00431 | 0.06 % | monotone, apparent order 9.58 |
| E W3 0–2 mm | +0.00270 | +0.00261 | +0.00259 | 0.53 % | monotone, apparent order 4.65 |
| E F36 0–3 mm | -0.00733 | -0.00732 | -0.00711 | 2.90 % | non-monotone |
| E W3 3–10 mm | +0.01737 | +0.01764 | +0.01787 | 1.26 % | monotone, apparent order 0.44 |
| E W3 Δ10–40 mm | +0.01973 | +0.02004 | +0.02025 | 1.03 % | monotone, apparent order 0.99, GCI_fine 2.60 % (indicative; non-uniform refinement) |
| E F36 Δ10–40 mm | -0.02006 | -0.02164 | -0.02392 | 9.55 % | non-monotone |
| E W3 bottom salt supply | -0.21526 | -0.21509 | -0.21497 | 0.06 % | monotone, apparent order 0.81, GCI_fine 0.18 % (indicative; non-uniform refinement) |
| E total salt | -0.00159 | -0.00229 | -0.00305 | 24.88 % | non-monotone |

| per-arm quantity (24 h) | arm | coarse | medium | fine | medium→fine rel |
|---|---|---:|---:|---:|---:|
| W3 Δ0–3 mm (g) | C1 | 0.10457 | 0.10522 | 0.10563 | 0.39 % |
| W3 Δ0–3 mm (g) | C0 | 0.10014 | 0.10091 | 0.10132 | 0.41 % |
| F36 Δ0–3 mm (g) | C1 | 0.04311 | 0.04191 | 0.04098 | 2.28 % |
| F36 Δ0–3 mm (g) | C0 | 0.05044 | 0.04923 | 0.04809 | 2.37 % |
| F36 Δ10–40 mm (g) | C1 | 0.09517 | 0.09628 | 0.09644 | 0.17 % |
| F36 Δ10–40 mm (g) | C0 | 0.11522 | 0.11792 | 0.12037 | 2.03 % |
| interface net salt c→f (g) | C1 | 0.25679 | 0.25708 | 0.25740 | 0.12 % |
| interface net salt c→f (g) | C0 | 0.00000 | 0.00000 | 0.00000 | – |
| W3 net downward salt @3 mm (g) | C1 | -0.00749 | -0.00724 | -0.00684 | 5.74 % |
| W3 net downward salt @3 mm (g) | C0 | -0.10014 | -0.10091 | -0.10132 | 0.41 % |
| F36 net downward salt @10 mm (g) | C1 | -0.28898 | -0.28782 | -0.28736 | 0.16 % |
| F36 net downward salt @10 mm (g) | C0 | -0.12500 | -0.12231 | -0.11986 | 2.05 % |
| F36 core descending volume fraction (–) | C1 | 0.08295 | 0.16859 | 0.11405 | 47.82 % |
| F36 core descending volume fraction (–) | C0 | 0.22789 | 0.22057 | 0.21828 | 1.05 % |

Persistent-downflow onset (1e-8 m/s, 3 frames), F36 [all, core] h: G_coarse C1 [6.833333333333334, 10.5]; G_coarse C0 [14.0, 14.5]; MEDIUM C1 [6.666666666666666, 10.166666666666666]; MEDIUM C0 [14.0, 14.166666666666668]; G_fine C1 [6.666666666666666, 10.166666666666666]; G_fine C0 [13.833333333333334, 14.166666666666668]. W3: none in any case.

Registered gate counts medium→fine (pass/fail/n.a.): surface_change 14/2/0; surface_inventory 16/0/0; surface_change_0_2 0/0/16; deep_change 14/2/0; bottom_salt 16/0/0; vertical_transport 47/1/0; core_descending_vf 2/1/13; interface_net 4/0/0; interface_pos 4/0/0; interface_liquid_net 4/0/0; effect 27/5/0; onset 8/0/0. Full rows: `analysis/compare/gates.csv`.

### 4.2 Time step: max dt 300 s → 150 s (medium mesh, B=1, both arms)

Runs: A `C1B1_24h`/`C0B1_24h` (dt 300, reused after identity check) vs v11 `T150_C1B1`/`T150_C0B1` (629 accepted steps each; 3.45 h and 2.61 h wall). Output interval stays 600 s; the evaporation clock and frames are identical.

Result: every registered working tolerance is met, by a wide margin.
- Surface 0–3 mm inventory change since t=0, both sides, both arms, 4/8/12/24 h: worst relative difference 0.29 % (tolerance 2 %).
- Cumulative net coarse→fine interface salt 0.02 %, gross forward 0.06 %, liquid volume 0.01 % (tolerance 5 %).
- Deep (10–40 mm) inventory change worst 3.3 % (early, 4 h, when the change itself is ~1e-4 g), vertical salt transport at 3/10/20 mm worst 0.30 %, bottom supply 0.04 %.
- Persistent-downflow onset (1e-8 m/s, 3 frames): identical except C0 F36 core 14.17 h vs 14.33 h (one output interval, within the 10-min criterion).
- Paired effect: E_1(W3 0–3 mm, 24 h) = +0.004313 g (dt 300) vs +0.004317 g (dt 150), i.e. 4.6e-6 g (0.11 %). Over all registered effect metrics the worst relative change is 4.1 % (deep-band effect at 4 h, |E| ~1.5e-4 g); surface effects ≤1.6 %.

The temporal discretisation error at dt=300 s is therefore at least two orders of magnitude smaller than E_1 for the primary metric. This says nothing about spatial error.

### 4.3 Perturbation phase (seed 2, 3) and amplitude (σ 3e-6, 3e-5), medium, dt 300

| pair | E W3 0–3 mm 4 h | 12 h | 24 h | E W3 0–2 mm 24 h | E F36 0–3 mm 24 h | onset F36 core C1/C0 (h) |
|---|---:|---:|---:|---:|---:|---|
| MEDIUM | +0.00083 | +0.00422 | +0.00431 | +0.00261 | -0.00732 | 10.166666666666666/14.166666666666668 |
| S2 | +0.00083 | +0.00422 | +0.00431 | +0.00261 | -0.00714 | 10.166666666666666/14.5 |
| S3 | +0.00083 | +0.00422 | +0.00431 | +0.00261 | -0.00842 | 10.166666666666666/14.333333333333332 |
| A3e-6 | +0.00083 | +0.00422 | +0.00431 | +0.00261 | -0.00776 | 10.166666666666666/15.5 |
| A3e-5 | +0.00083 | +0.00422 | +0.00431 | +0.00261 | -0.00716 | 10.166666666666666/13.0 |

### 4.4 Parameter endpoints (measured Ks replicate range; §6)

- P1: pending
- P2: pending

### 4.5 B=0 extension (interaction), fine grid and dt 150 s

- MEDIUM: E_0(W3 0–3 mm, 24 h) +0.00833 g; E_1−E_0 -0.00401 g.
- G_fine: pending
- T150: pending

## 6. Parameter-uncertainty review

Source: `experimental_data/DARUS-6478/.../F36 & W3 Sand Hydraulic Properties.xlsx` (SHA256 d63221c0…, read with formulas; dump `analysis/hydraulic_workbook_dump.txt`).

| quantity | replicate record | model value | traceable interval used |
|---|---|---|---|
| Ks F36 | 3 packings × 3 repeats: 658/669/669, 681/675/656, 624/640/645 cm/d (7.3–7.9e-5 m/s); packing means 7.77/7.77/7.40e-5 m/s | k=7.819e-12 m² (= mean 7.644e-5 m/s via k=Ks·μ/(ρg), μ=1.002e-3, ρ=998, g=9.81, the workbook's own conversion) | 7.3–7.9e-5 m/s (−4.5 %/+3.3 %) |
| Ks W3 | 3 packings: 2.6/2.7/2.7, 2.7/2.7/2.7, 2.7/2.7 cm/d; m/s sheet 3.0–3.2e-7; sheet means use the first 2 repeats | k=3.2034e-14 m² (= 3.133e-7 m/s) | 3.0–3.2e-7 m/s (−4.3 %/+2.1 %) |
| porosity F36 | Table 2 (250 mL): 0.3939/0.3989/0.3897; oven drying (100 cm³): 0.3980/0.3970/0.3992 | 0.40 | model value lies above every replicate |
| porosity W3 | 0.3483/0.3632/0.3494; 0.3471/0.3572/0.3637 | 0.36 | 0.347–0.364 |
| Brooks–Corey pe, λ, Swr | single least-squares fits per sand to pooled replicate curves; no reported interval | as fitted | none (refitting would be a new fit) |
| D0, tortuosity, D_eff, dispersion | no independent record | inherited laws | none |

Limits: the replicates are separate laboratory packings (cylinders 5 cm × 8 cm; 100 cm³ rings), not the MRI column. Their spread is a lower bound on the column's parameter uncertainty; packing differences between test cylinders and the experiment column are unquantified. No retention-curve or diffusion interval exists, so no statement can be made that any effect exceeds the parameter uncertainty as a whole.

## 7. Archive, hashes, resources

- 17 run directories archived to `runs_archive/` with per-file SHA256 verified on both ends; large verified files then released individually on liqin (`RELEASED_INDEX.json` kept remotely and locally).
- Perturbation bookkeeping and acceptance per extracted case: `analysis/perturbation_and_acceptance.json`.

## 8. Inference limits

- Grid/time-step/perturbation results are a finite scenario envelope of registered variants; they are not confidence intervals and do not cover unknown errors. Passing them is not parameter robustness and not experimental validation.
- Parameter coverage: only the measured Ks replicate range (separate lab packings, a lower bound on column uncertainty). No interval exists for D0/tortuosity/D_eff, dispersion or retention parameters; porosity corners were registered as not run. Hence no claim that the effect exceeds parameter uncertainty in general can be made.
- Plume-structure metrics (core descending fraction) are grid-sensitive and non-monotone; plume structure is not grid-converged even where inventories are.
