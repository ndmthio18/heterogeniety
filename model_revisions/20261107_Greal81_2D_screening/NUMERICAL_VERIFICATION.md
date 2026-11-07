# Numerical verification ledger

## Preregistered gates

1. Geometry: exact physical sand volume, top area and primary direct-interface
   area; positive orthogonal cells and affine TPFA flux reproduction.
2. Causal residual/Jacobian: all C1/C0 and B1/B0 settings on both supply
   variants. C0 mass rows must be exact zero; heat conduction must remain.
3. Shared-filter topology: Configuration B retains nonzero cross-filter
   hydraulic communication when the direct sand interface is blocked.
4. Conservation: independent material water, total-salt and energy ledgers in
   4 h short runs for A and B, with the established `1e-6` declared bounds.
5. Performance: 1/2/4 thread benchmark before choosing concurrency.
6. Early 2D/3D comparison: common accepted times, with no demand for exact
   plume or onset reproduction. The large screen is stopped if the relevant
   hydraulic supply direction or connectivity response is qualitatively lost.

## Current evidence

- Static input generation: passed (15 unique physical combinations, 30 B1
  cases; three A/B overlaps deduplicated).
- Primary mesh metrics: 4080 sand / 4692 filter cells; exact nominal volume,
  top area and 0.002 m2 direct interface by construction.
- HPCC build attempt 01 (`16345621`): failed before linking because the
  isolated CMake target did not expose the application directory to the local
  DuMuX overlay's relative `phase_equilibrium.hh` include. The log is retained;
  this is a build-path failure and no physical/numerical setting changed.
- HPCC build attempt 02 (`16345643`): completed with return code 0 after adding
  only the application-local include path. The resulting frozen solver SHA256
  is `9cec97585b65401943263e767bbb92765870eb6aa61946e119171d27ad251ca2`.
- Eight causal/geometry selftests (`16345669`--`16345676`): all completed with
  return code 0 and an explicit `passed` record. The primary physical interface
  area is 0.002 m2 (roundoff only); C0 advective, diffusive and Jacobian mass
  rows are exactly zero; C1 rows are nonzero; B0 has zero salinity-density
  response while retaining the thermal response. Configuration B contains six
  communicating filter cross-faces, whereas Configuration A intentionally has
  none.
- The A/B 4 h conservation cases reached 21.6 ks and passed. Their maximum
  relative water residuals are `2.11e-13` and `5.13e-14`, total-salt residuals
  are `2.12e-13` and `6.01e-14`, energy residuals are `1.82e-10` and
  `1.63e-10`, and complementarity residuals are below `6.1e-30`. The complete
  machine record is `m0_acceptance.json`.
- The 1/2/4-thread wall times were 579.32, 444.38 and 495.98 s. Two threads
  achieved only 0.652 efficiency and four threads only 0.292; the jobs also ran
  on different nodes. One thread per case was therefore selected to maximize
  case-level throughput, initially capped at eight concurrent cases.

No parameter-screen result is accepted or interpreted at this stage.
