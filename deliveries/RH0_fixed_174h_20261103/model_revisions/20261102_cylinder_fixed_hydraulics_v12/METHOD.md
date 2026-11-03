# RH=0 fixed porosity and permeability: isolated diagnostic v12

User confirmed on2026-11-02: retain precipitation and total salt conservation, fix BOTH porosity and permeability. Temperature remains293.15 K. No thermal simulation or refit is authorized by this implementation; that is a separate assessment.

Parent: frozen20261030_cylinder_precip_v09_r02, binary1ab6cfb632f7bf0a603ba83e8e00f810c0096af80ec534e3f776e0618e1efb10. Parent sources and all results remain untouched.

## Changed mechanism

`Revision.FixedHydraulics=true` makes the volume-variable porosity used by fluid storage, diffusion and reaction capacity equal to each material's initial reference porosity (.40/.36). The intrinsic permeability is the initial value (7.819185772155931e-12/3.2034098778596945e-14 m2). Relative permeabilities still depend on saturation; salinity still affects density, viscosity, activity and transport. There is no changed gas-film thickness, saturation law, diffusivity multiplier or external-total normalization.

The solid NaCl unknown and density conversion remain in the total-NaCl conservation row and equilibrium complementarity equation. In this diagnostic, the stored solid variable is an **equivalent solid volume per original bulk volume used for inventory only**, not an occupied geometric pore fraction. SolidState's underlying fractions are not altered to compensate inert-solid mass. Hydraulic porosity is overridden consistently before effective diffusion is evaluated. This is an isothermal-only mechanistic removal of pore filling, not an external efflorescence/crust-growth model. Solid inventory beyond initial pore capacity is explicitly not interpreted as physical pore occupancy; no clipping or disappearing salt is allowed. Historical `precip_vf_max` and VTK solid-volume labels retain their names for parser compatibility but have this inventory-equivalent meaning when FixedHydraulics=true.

Default false preserves the old constitutive path. Every accepted-step audit additionally verifies exact reference phi and K when enabled. Temperature remains isothermal and the existing nonisothermal guard remains enforced.

## Gates and comparisons

1. Frozen-dependency compile; inherited21 fluid-equilibrium/5 recoverable invalid-trial checks.
2. Actual volume-variable/storage selftests for both materials: solid-equivalent fractions .001,.01,.1 (plus .45 only in fixed mode), nonzero-solid total salt storage, fixed water/air storage, fixed K and fixed effective diffusivity; coupled mode must retain pore loss/K decline.
3. Legacy coupled precipitation600 s vs archived parent budget (new switch false); six fixed precipitation/dissolution reaction runs at maxdt30/15 s with mass balance<1e-6, equilibrium constraints and endpoint difference<0.5%; original-grid coupled/fixed2 h+10 min regressions vs v08; inherited injected timestep rollback case compared with fixed15 s endpoint.
4. Only after these pass, one174 h run from original initial state. While running, compare its budget prefix at24 h to v08, and at57.5 h (before parent's first positive solid) to r02. Do not compare to the old65.1667 h prefix as identical because the intended mechanism has then changed. Record checks after crossing65.283205529 h; do not claim full174 h completion until reached and terminal acceptance passes.

Short gates are not full-window convergence. Fixed-mode initial conditions with nonzero solid differ in fluid storage from coupled-mode reaction tests; compare dt pairs within the SAME mechanism, not their different physical initial inventories. The diagnostic's absence of blockage cannot validate its physical applicability.

## Frozen run and resources

RH0, delta8.100162249880822 mm,2 h pre-equilibration plus174 h evaporation, original30720-cell cylinder, sigma1e-5 seed1,300 s maxdt,600 s spatial output, originalNewton/retry/phase/budget limits. No post24 h fitting. Main wall cap48 h; max2serial gate solvers CPU6/7, one productionCPU6,threads1,nice10. Existing workstation liqin execution arrangement retained; no shared dependency edits.

Remote code: /home/zhixin/Documents/Cooperation_Ali/model_revisions/20261102_cylinder_fixed_hydraulics_v12
Remote raw: /tmp/zhixin_cylinder_fixed_hydraulics_v12_20261102
Scratch reserve4 GiB; prelaunch need12 GiB. Only own new VTUs may be replaced by gzip after decompression/hash verification; no old revision removal. A terminal failure also archives the last uncompressed fields. Local incremental backup verifies hashes. Do not restart or adjust settings for slowness. All failed attempts retained.

Deliver comparison of actual evaporation/reservoir loss, dissolved+solid salt inventories, concentrations and downflow with the accepted old prefix, and experiment on matched observation/time definitions. First saved positive solid is a model equilibrium event, not experimental nucleation. Retain known missing-crust and nonisothermal physics limitations.
