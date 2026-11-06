# Progress

- 2026-11-06: Created isolated branch `research/greal81-coupling-regime-map`
  from verified Greal-81 commit `469b6a95edd685a990dc7fea1780221be571d3a9`.
  Audited v10 causal controls against the explicit-filter nonisothermal model.
  Ported residual/Jacobian-level Darcy/Fick controls, restricted C0 to the
  direct sand-sand interface, preserved P3-filter communication and thermal
  conduction, and retained local-temperature density response under B0.
  Portable HPCC binary r03 SHA256 is
  `daacab36ed1e16057e4db325aebf39aab22737e74232ac45ea8826059e07156c`.
  Four production-mesh causal self-tests passed as Slurm jobs
  `16330660`--`16330663`: C0 gives exact-zero direct F36--W3 water/salt flux
  and mass-row Jacobian while preserving the thermal Jacobian; B0 removes the
  salinity density response while retaining the temperature response and the
  explicit P3 filter path. Original/patched C1B1 24 h regression jobs
  `16330674/16330675` are running. M1 production remains held until their
  normalized full-state and conservation comparison passes.
