# Implementation audit

## C0/C1: direct material-interface exchange

`CausalDarcysLaw` and `CausalFicksLaw` are registered as the actual DuMuX
advection and molecular-diffusion property types. Therefore the switch acts in
the residual, numerical Jacobian, upwinding and accepted conservative fluxes.
`Problem::interfaceExchangeBlocked` selects only direct F36--W3 sand faces;
sand--filter faces, the central reservoir boundary and flow inside the P3
filter remain active.

C0 returns exact zero for two-phase Darcy flux and all-component Fick flux on
those faces. It does **not** block the energy-conduction operator. The
production-mesh audit therefore tests exact-zero non-energy Jacobian rows and
requires a nonzero energy row. Requiring the whole block to vanish would
silently contradict the task's demand to preserve thermal conduction.

## B0/B1: salinity contribution to buoyancy

For the liquid gravity term only,

`rho_g = rho_ref(p,T,x_1M) + lambda*(rho-rho_ref)`.

`lambda=1` calls the original upstream Darcy law. `lambda=0` retains local
pressure and temperature dependence in `rho_ref`, as well as ordinary gravity.
Actual composition remains in storage, viscosity, diffusion, water activity
and every non-buoyancy constitutive relation. The bottom hydrostatic driving
term uses the same convention.

## Greal-81 integration differences from v10

The v10 mesh had no explicit common P3 filter. Consequently its C0 global
cross-side residual and full off-diagonal Jacobian could vanish. Greal-81
retains an indirect F36--P3--W3 pathway and nonisothermal heat conduction.
Accordingly, the valid Greal-81 gate is local to direct sand-interface
water/salt transport; global half-domain independence is neither expected nor
claimed.

No air-film, bottom-hydraulic, equilibrium-precipitation, porosity,
permeability, water-activity or nonlinear tolerance parameter was fitted or
changed in this port.
