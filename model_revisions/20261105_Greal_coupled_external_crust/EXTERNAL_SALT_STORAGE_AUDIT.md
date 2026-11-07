# Inventory separation implementation audit

The inherited mineralization storage accesses solidVolumeFraction(0). The local mineralization overlay now routes this accessor to an explicit inventorySolidVolumeFraction accessor. Equilibrium storage continues to add this one inventory to NaCl and zero the algebraic mineral row.

The underlying volume-variable update saves the inventory before clearing component 0 in the physical solidState for actual top-boundary cells. The inert matrix remains 1-phi0. Hydraulic phi/K remain fixed. Thermal properties are then evaluated from that physical state. Deeper cells retain their existing interpretation; a significant-deeper-solid stopping gate remains to be implemented.

External solid sensible heat is represented once by n_s/V * M_NaCl * cp_NaCl(T) * T, added to the nonlinear energy storage and the audit ledger by the same accessor. This uses the accepted sensible-energy reference and a lumped external-salt/surface-cell temperature assumption. It introduces no additional conductive resistance. The exploratory 174 h ledger closed numerically, but controlled Gate E and dynamic sensitivity evidence remain incomplete; numerical closure alone does not establish physical adequacy.

The constitutive height uses the specified 2165 kg/m3 geometric density, while molar inventory retains the solver's solid molar density. These distinct conventions must remain explicit.
