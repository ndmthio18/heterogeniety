# Conventional 2D mechanism track

Task: TASK_2D.md. Source and runs are isolated in track2d. Existing 3D files/runs retain their paths; track3d/README.md indexes them without moving live directories. Both tracks use the frozen nonisothermal v13 activity, phase composition, equilibrium solid inventory, fixed phi/K, thermal/fluid laws, reservoir1M/20°C/20mm head, RH0 and8.100162249880822mm film. No fit, imposed total evaporation, clock shift or concentration correction.

## Geometry and normalization

The conventional plane is50mm wide and40mm high, divided at x25mm. UGGrid2 with standard orthogonal CCTpfa replaces the custom cylindrical UGGrid3 geometry. A constant extrusion W_eff=π(25mm)²/50mm=39.26990817mm multiplies every FV volume/face consistently: nominal cylinder total sand volume/top area are preserved. The sand x discretization is100 columns; the40 original graded vertical layers are retained (4000cells), with6×100 added filter cells when enabled (4600cells). The targeted refined mesh doubles x and sand vertical resolution; no full-window convergence claim.

The old1.001608189 polygonal-top area correction is removed (set1), because the planar top already has exactly the nominal circle's area. This is geometric accounting, not film refitting. The 3D polygonal sand volume differs from the nominal circular volume by about0.16%. In-plane side and bottom walls keep the same heat flux law. A conventional2D plane has no front/back wall exchange, so it does not reproduce the cylinder's perimeter-to-volume heat exchange or3D fingers. Absolute2D–3D evaporation/onset/profile matching is not required or implied. Depth enrichment comparisons are against each dimension's own B0.

Initial random phases/seed/amplitude follow the frozen physical-space perturbation with the z term omitted, then sand-only zero-mean/RMS normalization and exact total-salt correction. This is a documented dimension change; it does not preserve3D instability morphology.

## Bottom matrix and slit mapping

Common B resistance uses the same dimensional values as3D:0,28885.60397653,288856.03976530,2888560.39765299 Pa s/m. The original coarse bottom half-cell remains2.030005mm; spatial refinements keep physical Rf fixed rather than renormalizing to a new cell size.

The4.5mm explicit filter spans the full width, phi0.35 and K1.7333127738454676e-11m², with the same declared unmeasured retention/thermal surrogate as3D G. No extra Robin resistance. The lower port becomes a centred slit with width A_port/W_eff. Hypothetical3D diameters2/5/10mm map to slit widths0.08/0.50/2.00mm. Equal integrated open area, identical initial K/mu and lower half-cell thickness imply equal initial bottom-face conductance K*A/(mu*d_half). This does not match3D spreading resistance or later flow patterns. Exact interval/face overlap preserves open area; the smallest slit is subcell. G1/G2 targeted refinement screens must bound interpretation. No plenum reconstruction or measured port dimensions are claimed.

## Source and numerical checks

Solver Frodo build SHA b327666ace7f6e5ae8702dde7e12f06ca58e4f3cc80b30fed7a99403081c4a4a; sal relocated ELF4f1415869d963d3e77bc6ff19b4200b5cbe4035c57e26ce3bb43ba424f329836. Same pinned dependency tree/runtime as the accepted short-window accelerated3D build; source/compile/input manifests retained. Source changes are geometry, scalar extrusion, dimension-correct diagnostics and mapped slit; thermodynamic/transport/mineralization headers retain exact3D bytes.

The Frodo core controller (sal19195 was never started and cancelled after authorized host change) requires existing3D zero-change gate, actual fixed/coupled storage probes, six reaction/dt gates, injected rollback, all four actual bottom area/donor/enthalpy probes, static7200s B0, short evaporation, doubled-extrusion invariance and B0 dt150/refined screens. G gates additionally check each filter hydrostatics/storage and G1/G2 dt/refined screens. Short-profile normalized RMSE must be below5% to pass the registered screen; this deliberately coarse acceptance is not an error estimate justifying smaller physical differences. Report actual differences before scientific claims.

Water/salt/energy and separate sand/filter ledgers are checked at every accepted step. Native face gross fluxes retain both signs before aggregation. Field-based dissolved/solid salt is independently matched to the ledger. Solid density2165kg/m³ and molar mass0.0584428kg/mol are verified against the pinned NaCl component; equivalent solid volume is inventory only, never physical pore occupancy.

All jobs start from original initial conditions. No saved VTU restart, physics/tolerance adjustment or film refit. Compilation/transfer hashes passed. Core numerical gates passed. B0–B3 completed174h with verified backups; G1_refined failed, so G production remains blocked. Initial supervisor2788162/controller2788169 are historical identifiers, not a current-running claim. User authorized Frodo/cxhpc after initial sal submission. Frodo has12physical cores,~22GiB available RAM and237GiB scratch, near-idle at admission. Six serial slots use50% of physical cores. cxhpc was also checked through its existing liqin bridge but not needed.
