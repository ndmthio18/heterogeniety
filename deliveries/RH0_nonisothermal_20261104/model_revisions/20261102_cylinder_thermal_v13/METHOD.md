# Independent non-isothermal RH=0 cylinder calculation (v13)

## Scope

- Independent source, binary, scratch output and provenance from v12.
- Same 3-D cylinder mesh, RH=0, fitted gas-film thickness `8.100162249880822 mm`, equilibrium precipitation, and fixed initial porosity/permeability as v12.
- Initial porous medium, reservoir and laboratory ambient temperature: `293.15 K`.
- No refitting of evaporation, heat-transfer or hydraulic parameters.

## Thermal closure

- The energy equation is enabled (`NONISOTHERMAL=1`).
- Surface saturation pressure, gas density and water-air diffusivity in the film are evaluated using the evolving surface/film temperature.
- Top sensible heat transfer uses air conduction over the same effective film thickness used for mass transfer.
- Side and bottom heat exchange use the pre-existing plexiglass conduction assumption, `k=0.184 W m-1 K-1`, `d=5 mm`, with the laboratory exterior held at `293.15 K`.
- Reservoir inflow carries liquid enthalpy at `293.15 K`; outflow carries local liquid enthalpy.

The plexiglass-only wall condition neglects external convective resistance and is therefore an explicit high-heat-replenishment baseline, not a measured thermal boundary. Crystallization enthalpy and external efflorescent-crust morphology are not represented.

## Acceptance before 174 h

1. Independent build and source hashes.
2. Closed reaction, dissolution and persistence gates at two time-step limits, run serially on CPU 7 while v12 remains on CPU 6.
3. Water, salt and regional salt budgets below `1e-6` relative residual.
4. Energy budget below `1e-6` relative residual.
5. Accepted temperatures remain within the fluid-system table range `(273.15, 323.15) K`.
6. Only after all gates pass may the 174 h case start on CPU 7; the existing v12 production remains on CPU 6.

## Interpretation

This calculation isolates the effect of the stated thermal assumptions. Agreement with the evaporation curve would not identify the true wall heat-transfer coefficient or validate the precipitation physics.
