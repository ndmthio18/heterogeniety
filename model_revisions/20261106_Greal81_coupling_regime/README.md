# Greal-81 coupling and regime-map campaign

This isolated revision ports the verified direct F36-W3 interface switch and
salinity-buoyancy switch into the accepted three-dimensional nonisothermal
Greal-81 model.  It preserves the explicit 4.5 mm P3 filter, central inlet,
thermal conduction, water activity, fixed hydraulic porosity/permeability and
8.100162249880822 mm reference gas film.

The causal intervention is deliberately narrow. `C0` blocks only direct
sand-sand Darcy and Fick fluxes above the filter. It does not sever indirect
communication through the common P3 filter. `B0` removes only the salinity
increment in the liquid gravity density; pressure, temperature, gravity and
all thermophysical storage/transport laws remain active.

Production is prohibited until the M0 self-tests and paired 24 h regression
pass. See `NUMERICAL_ACCEPTANCE.md`, `CASE_REGISTRY.json`, and `PROGRESS.md`.
