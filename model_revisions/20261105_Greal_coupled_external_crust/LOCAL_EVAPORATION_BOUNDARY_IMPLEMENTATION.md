# Enabled integration r01

The boundary evaluates the existing film driving state from current volume variables. It multiplies this signed water flux by a resistance computed from the inside SCV inventory and actual face area. The water-vapor enthalpy term uses the resulting flux. Original gas-side conductive heat and air enthalpy terms are retained.

Geometry rejects multiple atmospheric faces sharing a cell, rather than double counting inventory. Top cells are identified directly from finite-volume boundary faces, with no nearest-centre mapping. The mineral accessor overlay has a compile-time selection marker.

Newton trials use a smooth signed algebraic continuation of height/resistance near zero inventory. No primary variable is clipped. Nonfinite or nonpositive conductance denominators raise NumericalProblem for the established Newton retry path. Accepted states retain the existing negative-solid tolerance; signed roundoff-scale inventory remains in mass/energy ledgers. The positive-domain analytical helper tests alone do not validate this continuation; enabled integration tests are required.

An accepted-step total deeper positive solid inventory above 1e-9 mol causes a stop for review. The face-mass reconstruction checks the same tolerance plus 1e-14 kg rounding allowance. These are computational detection tolerances, not experimental detection thresholds.

The implementation supports external fraction 1 only, as requested for the first model. Disabled mode provides baseline recovery. The normal runtime guard rejects endpoints beyond 96 h unless `ExternalCrust.AllowUnqualifiedProduction=true` is explicitly supplied. The user-authorized exploratory 174 h calculation used that override; the override does not mark the outstanding gates as passed.

Compact `crust_budget.csv` records each accepted timestep for both sands. Selected-time W3 surface maps were reconstructed from native top faces and checked against the solver ledger. Targeted mesh/timestep sensitivity is still outstanding.
