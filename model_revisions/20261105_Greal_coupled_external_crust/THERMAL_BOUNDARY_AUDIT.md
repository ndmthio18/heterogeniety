# Thermal scope amendment

The user explicitly excludes the additional external-crust conduction process.

- ExternalCrust.ThermalResistance=false.
- Original gas-side conduction remains k_air(T_film)*(T_surface-T_ambient)/delta_air.
- The water-vapor enthalpy contribution uses beta times the original signed water mass flux.
- Original air-component enthalpy transport remains.
- Temperature, phase properties, water activity and diffusion coefficients remain coupled to the current solution.
- No extra latent heat sink is introduced.

This removes the need to select crust thermal conductivity. It does not remove the requirement to distinguish conservative external salt inventory from physical internal solids in heat storage and conductivity. That separation was implemented, and the exploratory 174 h energy ledger remained numerically closed. The run was user-authorized before all controlled gates passed, so this evidence is not a complete thermal verification.
