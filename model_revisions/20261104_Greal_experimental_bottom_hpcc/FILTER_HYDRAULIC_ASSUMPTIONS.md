# Filter hydraulic assumptions

G-real uses the measured P3 mean saturated permeability `5.30e-12 m2` exactly once, inside the explicit porous filter. `Revision.FilterHydraulicResistance=0`, so no second Robin resistance is imposed.

The reservoir pressure is evaluated from a water level 20 mm above the sand/filter interface. The explicit-filter implementation intentionally does not add the filter's 4.5 mm geometric offset to this datum.

Only saturated permeability is experiment-constrained. Porosity 0.35, the inherited Brooks-Corey curve, residual saturation, relative permeability and thermal properties remain provisional. Consequently, passing hydrostatics and conservation establishes implementation consistency, not physical validation of unsaturated filter behavior.

The boundary self-test perturbs both sand-side donor states in both flow directions and checks component upwinding and enthalpy. Its accepted evidence is stored remotely under `gates/boundary`; all failed deployment attempts are retained separately.
