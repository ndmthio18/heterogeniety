# Numerical acceptance gates

1. Source/input hashes and portable build manifest are recorded.
2. Four production-mesh switch self-tests pass.
3. C0 gives exactly zero direct sand-interface Darcy/Fick flux and all
   non-energy rows of the cross-interface Jacobian while retaining both the
   original thermal-conduction row and nonzero P3-filter lateral flow.
4. B0 gives exactly zero response of the gravity term to a salinity-only
   perturbation and a nonzero response to a temperature perturbation.
5. Patched C1B1 reproduces a paired original-solver 24 h run with maximum
   normalized state discrepancy no larger than `1e-7`; accepted time grid,
   water/salt/energy budgets, temperature, saturation and reservoir loss are
   compared explicitly.
6. Water, salt and energy residuals remain within the accepted Greal limits.

Thresholds are not relaxed automatically. A failed gate stops production.
