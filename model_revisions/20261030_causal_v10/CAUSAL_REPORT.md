# v10 2×2 causal control: material contact × salinity buoyancy (RH = 0, 24 h)

Executor: Opus A (`claude-opus-5-5`), 2026-10-30/31. Protocol: `model_revision_plan/20261030_opus_campaign/PLAN.md` (section "Opus A"). Build `v10c`; handoff `HANDOFF_READY.json` (SHA256 `f92190a2…`), snapshot `snapshot_v10c.tar.gz` (`39344707…`).

## 摘要（中文）

* 在 v08 `Dry_trial02_r02` 冻结基准上实现了两个因果开关（`Revision.InterfaceExchangeEnabled`、`Revision.SalinityBuoyancyScale`），作用于求解器实际装配的 Darcy/Fick 通量定律。默认开关与 v08 **逐位一致**：24 h 全部预算列与 0/2/4/8/12/24 h 全部 VTU 场差值为 0.0，接受步时刻完全相同。
* 隔断在装配层面严格为零（界面通量、界面 Jacobian 块、另一侧扰动下的残差变化均为 0.0）；λ=0 时 Darcy 重力项与盐度无关（逐位），1 M 静水下 λ=0 与 λ=1 逐位相同。四个 24 h 算例全部完成，分区预算残差 ≤7×10⁻¹³，独立场积分与账本差 ≤8×10⁻¹⁵，无析盐。
* **主指标 W3 0–3 mm 表层盐库存的连接效应很小**：E₁ = +0.0003/+0.0008/+0.0023/+0.0042/+0.0043 g（2/4/8/12/24 h），为隔断案例同期增量的 2–7 %；E₀ = +0.0083 g（24 h）。交互项 E₁−E₀ = +0.0007 g（12 h）、−0.0040 g（24 h），时间上变号、量级与 E 相当，与 F36 羽流时序相关。
* **连接的主要作用是供液改道**，而非表层富集：连接后 W3 自身底部供盐由 0.237 g 降至 0.022 g、供水由 3.96 g 降至 0.36 g（−91 %），改由 F36 底部进入并经界面横向输入 W3（24 h 净 0.257 g 盐、3.54 g 水；平流全部为粗→细，扩散为细→粗 −0.035 g）。精确分解：ΔS_W3 效应 +0.042 g = 底部供给差 −0.215 g + 界面输入 +0.257 g。新增盐主要位于 W3 3–20 mm 次表层。
* 盐度浮力只在 F36 形成下行流（连接时核心诊断起点 10.2 h，隔断时 14.2 h；λ=0 无任何下行流；W3 在所有算例中无下行流），并使 F36 表层 0–3 mm 在 24 h 减少 0.044–0.048 g。
* **推断边界**：数值稳健性（网格/时间步/扰动）由 B 检验，尚未完成；目前不能声称 E 超出数值不确定度，也没有参数区间检验，更不是实验验证。由于交互项与 E 同量级且随时间变号，建议 B 执行 B=0 细网格/150 s 配对扩展。

## 1. Frozen baseline and scope

Base case `model_revisions/20261030_cylinder_film_v08/runs/Dry_trial02_r02`: full 3-D cylinder Ø50 mm × 40 mm, 30720 cells, coarse F36 (x ≤ 25 mm) / fine W3, 20 mm reservoir head, 1 M supply, 293.15 K, unified Pitzer water activity, predictive film δ = 0.008100162249880822 m, RH = 0, transfer multiplier 1, 2 h zero-evaporation pre-equilibration + 24 h evaporation, max dt 300 s, output 600 s, six-mode physical-space perturbation σ = 1e-5, seed 1. No re-calibration of the film and no normalisation to the weighed loss in any case; local and total evaporation respond to the solved surface concentration. The v09 174 h run, MRI data, older baselines and the shared DuMuX stack were not modified. This work tests numerical causal attributions inside the model; it does not address the MRI salt-recovery/weighing gap and is not independent experimental validation.

## 2. Implementation (build v10c)

**Source tree.** `source/` is a copy of the v08 tree used for `Dry_trial02_r02` (all files verified against the v08 build manifest, `baseline/baseline_manifest.json`; remote v08 source and binary `c9145e42…` re-verified). Input, mesh (`fc30b952…`) and forcing file are byte-identical copies. DuMuX 3.7 (`3aedc27f`) and the static dune-grid/UG libraries of v06 are only read (`libdunegrid.a ff274f30…`, `libduneuggrid.a 32df2876…`).

**Where the switches act.** In DuMuX 3.7 the 2pncmin residual obtains every interior-face component flux from `FluxVariables::advectiveFlux` (→ `AdvectionType::flux`, TPFA Darcy, then upwinding) and `FluxVariables::molecularDiffusionFlux` (→ `MolecularDiffusionType::flux`, TPFA Fick). Two derived laws (`source/appl/causal_flux.hh`) are registered as these property types, so the same laws are used by the Newton residual, the numeric Jacobian, the accepted-step audit, the least-squares velocity diagnostic and the VTK velocity output. No diagnostic is zeroed separately.

* `Revision.InterfaceExchangeEnabled` (default `true`). When `false`, an interior face whose two cells lie in different materials under the spatial-parameter rule (`x ≤ 0.025 m` coarse) returns exactly zero Darcy flux (both phases ⇒ zero advection of water, air, NaCl) and zero Fickian flux (all components, both phases). Zero-thickness impermeable partition: no cell removed; volumes, porosity, top area, film and the distributed bottom reservoir boundary unchanged. At start-up the problem verifies that the material-rule interface faces coincide with the geometric split plane (960 faces, 0.0020000 m², no cell centre on the plane).
* `Revision.SalinityBuoyancyScale` λ ∈ [0,1] (default 1). Liquid density in the Darcy gravity term: `ρ_g = ρ_ref(p_liq,T,x_ref) + λ(ρ − ρ_ref)`. `x_ref` is the 1 M reservoir liquid composition (water/air/NaCl mole fractions 0.98191160890 / 1.47065873e-5 / 0.01807368451; 1.000 mol/L; ρ = 1037.1995 kg m⁻³ at 1e5 Pa, 293.15 K), evaluated with the same fluid system at the local liquid pressure and temperature once per volume-variable update (`source/dumux/porousmediumflow/2pnc/volumevariables.hh`). The same `ρ_g` replaces `ρ` in the face-averaged hydrostatic term of the bottom reservoir face, `(ρ_res + ρ_g,cell)/2`; the reservoir head itself (`ρ_res`, 1 M) is unchanged. For λ = 1 the law calls the unmodified upstream function and the bottom face uses the actual density, i.e. exactly the v08 path. Gas-phase gravity keeps the actual gas density. Storage, molar densities, viscosity/mobility, diffusion, water activity, film flux unchanged. This is neither `g = 0` nor a global constant density.

**Diagnostics added (do not affect the solution; proven by the bitwise regression).** Per accepted step, `causal_budget.csv`: per side (F36, W3) component inventories, bottom inflow/outflow face sums, top fluxes, side ledgers; per side and depth band (0–2, 2–3, 3–10, 10–20, 20–40 mm; actual cell/band volume overlap of the extruded prisms) total and dissolved salt, liquid water and liquid volume; interface fluxes coarse→fine for water/air/NaCl, advective and diffusive, by face-height overlap with 0–2/2–10/10–20/20–40 mm, net and per-face positive/negative parts, plus liquid volume flux. `vertical_salt_flux.csv`: per side, advective (net, gross downward) and diffusive NaCl flux through each of the 39 horizontal mesh planes. `seed_event.json` adds per-side component and per-band salt impulses of the seed. Per-side water and salt ledgers `ΔN_i = −(boundary outflow)_i ∓ I − seed_i` are gated at < 1e-6 relative, like the global ones.

## 3. Gates (all passed before the handoff; `stages/v10c/*.json`)

| Gate | Result |
|---|---|
| Self-tests on the production mesh, all four settings (`Revision.CausalSelfTest`): states xU (hydrostatic 1 M), xP (same p, salinity ×(1 ± 0.3)), xF (xP + ±20 Pa) | configured law = definition on all 177 664 face orientations; λ=1 re-implementation − upstream = **0**; λ=0 interior Darcy flux and bottom driving potential salinity response = **0** (λ=1: 4.4e-15 flux units, 0.116 Pa); λ0−λ1 at uniform 1 M = **0**. Blocked: interface FluxVariables fluxes, Jacobian blocks between the two cells of every interface face, residual change of one half after arbitrary perturbation of the other half all **exactly 0** (same-side Jacobian 2.0e-4). Connected: 6.8e-6 / 7.4e-6 (coupling present). |
| Hydrostatic, 2 h, no evaporation, σ = 0 (C1B1, C1B0, C0B0) | ledgers ≤ 2.1e-13; λ=0 vs λ=1 all fields **identical (0.0)**; blocked vs connected 1.1e-15; |u| ≤ 3.2e-16 m s⁻¹ |
| Prefix regression, switch keys absent, 2 h + 10 min vs v08 | all budget columns and all VTU cell fields at 0/7200/7800 s **identical (0.0)**; identical step times; identical seed impulses |
| Short checks 2 h + 30 min (C0B1, C1B0, C0B0) | ledgers ≤ 2.8e-13; interface columns identically 0.0 in C0 |

Deviation from the plan wording: the unit-level checks were run on the production two-material mesh with designed states rather than on a separate small mesh; this tests the actual geometry, assembler and Jacobian, while a separate mesh would have required bypassing the inherited cylinder geometry gate.

## 4. Production runs (24 h, CPU 4, nice 10, 1 thread)

| Case | Contact | λ | Wall / CPU (h) | Peak RSS | Max rel. ledger residual (global, F36, W3) | C_max (M) | S_min | Precip. | Field vs ledger | Side closure (g) |
|---|---|---|---|---|---|---|---|---|---|---|
| C1B1 | yes | 1 | 2.04 / 2.03 | 224 MiB | 5.6e-13 | 3.383 | 0.9944 | 0 | 7.9e-15 | 1.1e-11 |
| C0B1 | no | 1 | 1.66 / 1.65 | 223 MiB | 6.8e-13 | 3.080 | 0.9995 | 0 | 7.1e-15 | 7.1e-12 |
| C1B0 | yes | 0 | 1.60 / 1.59 | 223 MiB | 3.5e-13 | 3.366 | 0.9944 | 0 | 8.3e-15 | 8.3e-12 |
| C0B0 | no | 0 | 1.21 / 1.21 | 222 MiB | 6.3e-13 | 3.080 | 0.9995 | 0 | 6.6e-15 | 6.3e-12 |

All runs reached exactly 93 600 s (24.000 h evaporation), 145 evaporation-clock frames, interface faces evaluated = 960 every step, all interface columns exactly 0.0 in C0. **C1B1 = v08 bitwise over the full 24 h** (all budget columns; all VTU fields at evaporation-clock 0/2/4/8/12/24 h; identical step times; `stages/v10c/production_C1B1_24h.json`, `regression_status: passed`, max difference 0.0). B independently confirmed C1B1 = v08 with its own extractor. The machine was fully loaded (v09_r02 on CPUs 6–7, B on CPU 5); per-step cost was ~1.5× v08's at mid-run, all far below the 6 h cap. Gates took 1.1 h; whole batch 19:16 UTC (first build) → 03:01 UTC.

## 5. Results

Clock: evaporation time t = time − 7200 s. Inventories at t = 0 include the seed impulse; cumulative fluxes are counted from the accepted step at 7200 s. Salt in NaCl-equivalent g (dissolved + solid; solid is zero in every frame). E_B(t) = S_W3(C1,B,t) − S_W3(C0,B,t). Files: `analysis/v10c/effects_table.csv`, `effects_timeseries.csv` (10-min grid), `side_decomposition.csv`, `interface_exchange.csv`, `vertical_transport_selected.csv`, `persistent_downflow.json`; per-case `results/v10c/<case>/timeseries.csv` (every accepted step), `frames.csv`, `profiles.npz`, `snapshots.npz`. Figures `analysis/v10c/fig1…fig5`.

### 5.1 Primary metric: W3 0–3 mm salt inventory (g)

| t (h) | C1B1 | C0B1 | C1B0 | C0B0 | E₁ | E₀ | E₁ − E₀ | E₁ / ΔS(C0B1) |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.06187 | 0.06187 | 0.06187 | 0.06187 | 0 | 0 | 0 | – |
| 2 | 0.07832 | 0.07801 | 0.07832 | 0.07801 | +0.00031 | +0.00031 | +0.000005 | 1.9 % |
| 4 | 0.09021 | 0.08938 | 0.09018 | 0.08938 | +0.00083 | +0.00080 | +0.00003 | 3.0 % |
| 8 | 0.10999 | 0.10769 | 0.10974 | 0.10769 | +0.00229 | +0.00205 | +0.00024 | 5.0 % |
| 12 | 0.12753 | 0.12331 | 0.12682 | 0.12331 | +0.00422 | +0.00351 | +0.00071 | 6.9 % |
| 24 | 0.16709 | 0.16277 | 0.17110 | 0.16277 | +0.00431 | +0.00833 | −0.00401 | 4.3 % |

E₁ peaks at ≈ +0.0052 g near 16 h and declines afterwards (fig1); E₀ grows monotonically. 0–2 mm sensitivity: E₁ = +0.0028 / +0.0026 g and E₀ = +0.0023 / +0.0056 g at 12 / 24 h. W3 mean solution concentration 0–3 mm at 24 h: 2.70 / 2.63 / 2.77 / 2.63 M (C1B1/C0B1/C1B0/C0B0). The relative column is the ratio to the partitioned run's own increase since t = 0 and is given only for scale; it is not a "connection enhancement percentage".

### 5.2 Where the connection effect goes (exact side ledger, B = 1)

| | W3, 12 h | W3, 24 h | F36, 24 h |
|---|---|---|---|
| ΔS connected / partitioned (g) | 0.1376 / 0.1208 | 0.2786 / 0.2366 | 0.1960 / 0.2402 |
| Effect on side inventory (g) | +0.0169 | **+0.0420** | −0.0443 |
| = bottom-supply difference (g) | −0.1101 | **−0.2151** | +0.2128 |
| + interface input, connected (g) | +0.1270 | **+0.2571** | −0.2571 |

Closure of this decomposition is < 1e-12 g. Band split of E₁ for W3 at 24 h: 0–3 mm +0.0043, 3–10 mm +0.0176, 10–20 mm +0.0157, 20–40 mm +0.0043 g; the added salt sits mainly below the 0–3 mm layer (W3 excess-salt centroid 6.0 vs 5.2 mm; 1.1 M enrichment depth 18.9 vs 16.4 mm). Domain total salt changes by only −0.0023 g (−0.10 %) at 24 h with B = 1 and +0.0001 g with B = 0.

**Supply rerouting.** With contact, W3's own base supplies 0.022 g salt / 0.36 g water in 24 h versus 0.237 g / 3.96 g when partitioned (−91 %); F36's base supplies 0.453 g / 7.65 g versus 0.240 g / 4.03 g. In the model the reservoir is a fixed-head, fixed-1 M boundary on each bottom face, so the partitioned halves are hydraulically independent; the rerouting is a property of the connected sand pair, not of a dynamic shared reservoir.

**Interface exchange (C1B1, cumulative 24 h).** Advective salt 0.2923 g, entirely coarse→fine (per-face fine→coarse advective part 0.0000 g); diffusive salt −0.0352 g (fine→coarse; it reverses only on a few faces, +0.0004 g); net 0.2571 g. Advective water 3.54 g coarse→fine (0–2 / 2–10 / 10–20 / 20–40 mm: 0.83 / 1.51 / 0.78 / 0.42 g). Salt bands (adv, net): 0.091 / 0.127 / 0.050 / 0.025 g. Lateral delivery also reduces the upward advective salt transport inside W3 (cumulative upward advection through the 9.72 mm plane 0.109 g connected vs 0.264 g partitioned).

**Evaporation.** Totals 8.174 (C1B1, = v08 8.1742 g) and 8.155 g (C0B1); W3 share 49.35 % vs 49.59 % (C1B1 vs C0B1). The connection-induced change of local evaporation is ≈ 0.01–0.03 g per side, small compared with the supply rerouting. Sample water storage change 24 h: W3 −0.10 g, F36 −0.07 g (C1B1).

### 5.3 Salinity buoyancy and plumes

* Downflow diagnostic (max downward interior LS Darcy speed > threshold for 3 consecutive 10-min frames, t ≥ 0.5 h). F36 core: C1B1 10.17 h (0.5× / 2× thresholds 10.00 / 10.50 h); C0B1 14.17 h (14.17 / 14.50 h). F36 whole half: 6.67 h vs 14.00 h. **None** for λ = 0 and **none in W3** in any case. My extractor reproduces the v08 extraction for the identical C1B1 fields (6.67 / 10.17 h).
* F36 core volume with q_down > 1e-8 m s⁻¹ at 24 h: 16.9 % (C1B1), 22.1 % (C0B1). Gross downward advective salt through the 3.0 mm plane in F36: 0.373 g (C1B1), 0.314 g (C0B1), 0 for λ = 0.
* Buoyancy effect on F36 0–3 mm at 24 h: −0.0438 g (connected), −0.0481 g (partitioned). On W3 0–3 mm: connected +0.0007 g (12 h) / −0.0040 g (24 h); partitioned ≈ 1e-10 g (W3 alone does not feel buoyancy in this window).
* Consequently the interaction E₁ − E₀ equals, to < 1e-9 g, the buoyancy effect on W3 in the connected pair. Its late negative sign is accompanied by stronger fine→coarse diffusion in the 0–2 mm interface band (−0.0156 g with λ = 1 vs −0.0097 g with λ = 0 at 24 h) after F36 plumes freshen the F36 surface. The F36 surface connection effect is dominated by plume timing (transient −0.030 g near 16.5 h when the partitioned F36 surface drains later, fig1).

## 6. Inference boundaries

1. Implementation validity is established at the level stated in §3–4 (bitwise default regression to v08 over 24 h; exact zeros where required; closed ledgers; independent field integration). This does not establish numerical convergence.
2. **Numerical robustness of E₁, E₀ and the interaction has not been assessed by A.** The paired grid/time-step/perturbation checks are B's task (`model_revisions/20261030_verification_v11`), running at the time of writing. Until B reports, it cannot be stated that any effect exceeds the measured numerical uncertainty (PLAN rule 3–4). Pairing on identical mesh/dt/seed removes common errors only partially and unquantifiably.
3. The W3 surface effect is small in absolute terms (≤ 0.005 g; 2–7 % of the partitioned change) and non-monotonic in time for B = 1. Its late behaviour is coupled to F36 plume timing, which is sensitive to the perturbation and discretisation; it should be treated as **unresolved** until B's envelopes are available. The supply rerouting (≈ 0.21 g salt, ≈ 3.6 g water per side) is one to two orders of magnitude larger and is the dominant model-native consequence of the contact, but it also awaits B's checks.
4. The interaction is of the same order as E and changes sign between 12 h and 24 h; I therefore classify it as material for the conclusions and recommend B's B = 0 fine-grid and 150 s pair extension (PLAN B, item 49). If that is not run, the interaction's numerical robustness must be reported as not adequately tested.
5. No traceable parameter-interval test was performed by A; nothing here is a parameter-robustness or confidence-interval statement, and none of it is experimental validation. The downflow threshold is a diagnostic, not a linear-instability or MRI-visible onset.

## 7. Failure and repair record

* `build_v10a`: compile error (dependent type name `Darcy::Scalar(NAN)`); `build_v10b`: parenthesis error introduced by the fix. Both retained with logs; `v10c` is the only build used.
* `extract.py` initially required `seed_event.json`; fixed (missing seed → zero impulses, flagged) and re-tested on gate runs before any production extraction.
* `sync_local.py` first attempted to overwrite the read-only local handoff; changed to fetch once and compare remote/local SHA thereafter (`handoff_remote_equals_local` in STATUS.json).
* The local monitor's `controller_alive` flag used `pgrep -f`, which can match its own ssh command, so it could not detect a dead controller by itself. Liveness during the runs was independently shown by the advancing `reached_hours`/`updated_utc` of `STATUS_remote.json`; the check now uses `ps | grep "[c]ampaign.py"` and the final STATUS records the controller as exited normally.
* No solver run failed, timed out or was retried. Dev runs (`/tmp/…/dev/`) used for pre-campaign self-test trials are retained and are not cited as evidence.

## 8. Provenance and data

| Item | SHA256 / location |
|---|---|
| Binary `build_v10c/heterogeneity_causal` | `cb57a84155efcfa9aed4d8aef49f8c72d4039b3c38bb9f32943b5fd354a4ee8a` |
| Snapshot `snapshot_v10c.tar.gz` | `39344707eb548296ff2cad7980a7ce0c10619a038b1bc62f5c1395a7f10aa703` (verified locally, `handoff_verification_local.json`) |
| `HANDOFF_READY.json` | `f92190a276e95763382992ad5df225b12843b85e86e90788b51fc79c0b4d9b6c` |
| Mesh `inputs/cylinder.msh` | `fc30b9525a8dc7daa2b255a5e2f5586be169d201f20506140f61974f6f19d233` |
| Inputs C1B1/C0B1/C1B0/C0B0_24h | `aa319f8a…` / `ea9acb1d…` / `f98a5bbd…` / `9708137c…` (`inputs/input_manifest.json`) |
| Key sources | `causal_flux.hh 678727f4…`, `causal_switches.hh 4f8b365c…`, `causal_selftest.hh fbd53b93…`, `problem.hh 61764ceb…`, `properties.hh d8c2843c…`, `main.cc e8b07412…`, `volumevariables.hh df143fac…` (full map in `build_v10c/build_manifest.json`) |
| Scripts | `campaign.py 8479ea4e…`, `extract.py 8b48975d…`, `analyze.py 6f3bd04c…`, `build.py 34bdc0b8…`, `prepare_inputs.py ead9a31d…` |
| Raw runs (liqin) | `/tmp/zhixin_causal_v10_20261030/runs/v10c/` (fields gzip-1, raw SHA checked after compression, index `compressed_fields.jsonl`; 820/754/808/703 MB) |
| Local copy | `archive/v10c/<case>/`, verification `archive/v10c/archive_verification.json` |

Build: `python build.py v10c` on liqin (vasca311 Python; single process; `flock /tmp/zhixin_hete_20261030_compile.lock`; `taskset -c 4`; nice 10; MemAvailable ≥ 6 GiB). Campaign: `python campaign.py v10c` (resumable; skips passed stages; interrupted runs are moved, never overwritten).
