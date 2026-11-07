# Verification status

C0 pre-precipitation regression passed on HPCC: jobs 16309348/16309349 completed at 7800 s with exit 0, elapsed 5m31s/4m55s. All numerical fields in budget, film_budget, mineral_budget and thermal_budget (47 rows each) and depth_profiles_compact (3840 rows) match exactly in saved CSV precision. Evidence: c0_comparison.json. This establishes disabled recovery over 2 h equilibration plus 10 min evaporation only, not post-precipitation or full-window equivalence.

Constitutive test compiled and executed on the existing Frodo toolchain with C++17: PASS. It covers inventory-to-height mass reconstruction for unequal areas, zero mass and external fraction, analytical vapor resistance at 0/0.1/0.5/1 mm for all four requested diffusivity ratios, infinite diffusivity, signed flux and monotonicity.

The final exploratory source compiled successfully. The portable release binary SHA256 was `4f6ef0c672e5e5c04e376c815e0c29f281a41f36359ce0c116de6000bb26df6d`; the Frodo-native executable used for the completed run had SHA256 `99775343b964856a5a3820cf5ed32e5603273783c8e269ffdd628ad5412028ee`. Executables are not included in Git.

The user subsequently authorized an unqualified exploratory release. The independent Frodo run completed the requested 2 h pre-equilibration plus 174 h evaporation with return code 0. Runtime geometry, external-inventory reconstruction, deeper-solid, complementarity and conservation checks remained active. Maximum absolute water/salt/energy residuals were about 1.72e-13 mol, 2.01e-15 mol and 6.03e-6 J; maximum deeper positive solid inventory was 8.14e-35 mol.

This completion does **not** mean Gates A–F all passed:

- Gate A: runtime face mapping and mass-reconstruction checks operated; the selected-time W3 reconstruction agrees with the solver ledger to 1.22e-19 kg, but no independent full mesh family was completed.
- Gate B: analytical resistance tests passed.
- Gate C: disabled recovery passed only over 2 h equilibration plus 10 min evaporation.
- Gate D: a post-onset 174 h coupled trajectory completed conservatively, but it was released before the preregistered controlled dynamic gate was completed.
- Gate E: the original conductive boundary was retained and vapor enthalpy used the corrected flux once; the added salt sensible-energy ledger closed numerically. Added crust conduction was explicitly excluded by user scope.
- Gate F: targeted top-cell, face-resolution and timestep sensitivity was not completed.

The completed calculation must therefore remain labelled exploratory. Outstanding work includes controlled post-onset regression, targeted mesh/timestep comparisons and independent physical assessment of external fraction, coverage and diffusivity ratio.
