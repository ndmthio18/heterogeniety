# Resistance screening — conditional, fixed driving state

The proposed dimensional crust diffusion range has not yet been verified against original full-text parameter definitions and temperature. It has therefore not been used as a literature-supported interval.

An explicitly hypothetical dimensionless sweep uses Dc/Da = 0.01, 0.05, 0.1, 0.25 and 1. Both diffusivities refer to the same film temperature in this ratio screening. The air film remains at its accepted thickness. At fixed baseline temperature and activity the ratio is `1/(1+h/(delta*r))`, with r=Dc/Da. This approximation does not recompute temperature, activity, liquid supply, F36 flux or salt redistribution.

Coverage is handled as parallel patches: `W3 factor=(1-f)+f*covered_patch_factor`, with height inversely proportional to f. Concentrating mass on less surface does not justify applying the larger patch resistance over all W3.

Greal-81 full-coverage terminal W3 reductions are 76.57%, 39.53%, 24.63%, 11.56% and 3.16% respectively. Integrating the estimated change over the saved hourly surface histories gives evaporated-water reductions of 5.711, 2.231, 1.287, 0.569 and 0.151 g. These are conditional water-vapor estimates, not predicted changes in reservoir solution loss. Reservoir salt supply and liquid storage can change in a coupled model, so these values must not simply be subtracted from measured solution loss.

Material mapping was checked against accepted `SplitAxis=0`, `SplitCoordinate=0.025 m` and `isCoarse` using x<=split. An initial postprocessing draft assumed a zero-centered coordinate; its result was rejected and overwritten by the corrected analysis before interpretation. Solver outputs were unchanged.

Completed checks: face-area integration matches both material ledgers and total top evaporation to 3.33e-16 g/h. Native temperatures and surface activity are supplied. Actual filmWaterFlux_ uses local surface vapor pressure and mean-film properties; reference-temperature diagnostic vapor pressures were not inverted for T. Fixed-state driving terms cancel in the screening ratio.

Literature update: ratio 0.01 is verified as a fitted comparator in 2010WR009677 section 5.1 paragraph 63, for a 30°C disconnected-supply experiment. Its transfer to G-real remains hypothetical; other ratios are analyst scenarios. No verified dimensional literature band is claimed.

R_air=delta/Da and R_crust=h/(r Da). The saved resistance ratio is dimensionless. Scaled resistances R_air*Da=delta and R_crust*Da=h/r have units m; absolute s/m values are not claimed without verified transport-property evaluation. See LITERATURE_AUDIT.md for access limitations.
