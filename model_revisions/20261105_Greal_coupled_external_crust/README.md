# Coupled external crust — exploratory implementation and 174 h run

The Frodo exploratory calculation in `/temp/zhixin/Greal_external_crust_174h_frodo_20261106` completed 174 h evaporation on 2026-11-06 with return code 0. It used eight threads, the original initial state, 2 h pre-equilibration, the accepted 8.100162249880822 mm gas film, `D_crust/D_air=0.08`, crust porosity 0.43, full within-face coverage, fixed hydraulics and no added crust thermal resistance.

The completed calculation remains **exploratory and not fully gate-qualified**. The user explicitly waived prior completion of the remaining numerical gates. The result therefore demonstrates that the proposed current-state coupling can run conservatively through 174 h; it does not validate the dry-crust assumption, the selected diffusivity ratio or the modeled crust morphology.

Reference: accepted Greal81; audit commit c817504312be0b9ab1b0dbdd59b38070b82b7227.
Working branch: research/greal-coupled-external-crust.

The HPCC release attempt reached 75 h and then stopped because the account file-count quota prevented further VTK output. It was not resumed. The Frodo calculation restarted from the original initial state and completed independently. See `USER_RELEASE.md`, `REPAIR_LOG.md`, `NUMERICAL_VERIFICATION.md` and `EXPLORATORY_174H_COMPLETION.md`.

The equilibrium salt inventory must remain in the NaCl storage equation exactly once. In the accepted source, equilibrium_localresidual.hh adds the mineral storage to the NaCl row and zeroes the algebraic mineral storage row. This path must be retained.

The coupled source separates the conserved equilibrium NaCl inventory from the physical in-pore solid state in atmospheric top cells. The inventory remains in the NaCl storage equation exactly once, while the physical solid fraction used by local material properties is cleared there. External-salt sensible heat is added once through the explicit inventory accessor. This design is documented in `EXTERNAL_SALT_STORAGE_AUDIT.md`; its controlled mesh/timestep sensitivity remains incomplete.

The top boundary already multiplies water mass flux by gas water enthalpy. Correcting that mass flux inside neumann() will also correct vapor enthalpy transport; a second latent heat sink must not be added.

User scope amendment: omit added external-crust thermal resistance. Set ExternalCrust.ThermalResistance=false. Retain the original gas-side conductive boundary and the nonisothermal equations. Corrected current-iteration vapor flux must still enter the existing vapor enthalpy term exactly once. No crust thermal conductivity is needed for this scope. This is a vapor-resistance-only external-crust approximation; it does not establish negligible real crust thermal resistance.

The completed run preserved the accepted water, salt and energy ledgers. The maximum absolute residuals were approximately 1.72e-13 mol water, 2.01e-15 mol salt and 6.03e-6 J energy. These numerical closures do not establish physical validation. Gate F and parts of the dynamic and thermal verification programme remain outstanding.

## Lightweight Git delivery

The Git branch contains source, inputs, tests, launch/analysis scripts, compact diagnostics, reports, figures and the extracted W3 surface animation data. It intentionally excludes solver executables, raw VTU/PVD fields and duplicate tar archives. The completed full-field Frodo output was not copied into Git.
