# Proposed Phase II design — not implemented

Keep the accepted 8.100162 mm air film, bottom geometry and filter parameters fixed for first mechanism tests. Introduce external crust mass per top face only after deciding a physical transfer criterion; an arbitrary fraction chosen to fit MRI is not a mechanism test.

## Conservative storage

Source audit: problem.hh source() equilibrium branch uses an algebraic complementarity row for solid, while the salt equation stores dissolved plus solid. The legacy kinetic branch has opposite salt/solid reaction rates but is not the active equilibrium formulation. campaign_diagnostics.hh includes both inventories. A new boundary inventory must extend this storage definition, not add a second sink/source.

Let N_internal be current solid inventory and N_external the added surface inventory. Transfer R_out of solid must enter internal storage with -R_out and external storage with +R_out. A precipitation rate cannot independently feed both stores. Dissolution must reverse the same exchange. Include external dissolved salt and liquid-water storage if a wet crust is represented. The summed domain-plus-surface salt budget must retain zero external salt loss through evaporation. Equivalent solid volume fractions above pore capacity cannot be reinterpreted as literal pore occupancy.

## Model A: disconnected or dry resistance

Resolve an evaporation-interface temperature and vapor concentration. Use water activity times saturation vapor pressure at that interface, with air-film and crust resistances in series only where the vapor path actually traverses both. Add crust conduction resistance h/k_eff and interface energy balance. Remove latent heat once at the evaporation interface; do not add a second latent sink to an existing gas enthalpy flux. Include sensible enthalpy consistently with the accepted residual formulation. Partial coverage uses parallel exposed and covered face areas.

## Model B: liquid-connected crust

A surface porous layer requires liquid pressure, dissolved salt, saturation, temperature and external solid storage, coupled conservatively to underlying sand. Darcy transport, capillary retention and relative permeability determine whether the outer evaporation surface stays wet. Evaporation then uses outer-surface activity and temperature. Do not retain a full dry-crust vapor resistance in series with an evaporation plane already at its outer surface. Contact loss/detachment requires a separate justified geometry/contact model.

## Parameter classification

Measured/experiment-constrained: nominal column geometry, P3 saturated permeability, approximate inlet, reservoir composition. Accepted assumptions: RH=0, fixed air-film thickness, initial/environment/reservoir temperature. Postprocessed: equivalent external height under specified mass allocation. Unmeasured: coverage, external fraction, pore connectivity, crust permeability/retention, k_eff, contact resistance and evolving detachment. Literature diffusivity must be checked for definition, porosity inclusion and temperature before use. The 2650 kg/m3 alternative is sensitivity only, not NaCl crystal-density evidence.

## Required validation before production

1. Zero crust exactly recovers the accepted boundary.
2. Constant dry slab reproduces analytical serial vapor and thermal resistances.
3. Closed precipitation/dissolution test conserves total water and salt across both stores.
4. Evaporation-only energy balance counts latent transfer once.
5. Wet connected slab satisfies imposed hydraulic and heat supply bounds.
6. Covered fraction 0/1 and vanishing thickness have correct limits.
7. Short G-real comparisons retain accepted conservation tolerances and separate F36/W3 fluxes.
8. Only after those gates, evaluate matched long-window effects without refitting the air film.

Phase II implementation and long simulations remain unauthorized until review of the completed Phase I assessment.
