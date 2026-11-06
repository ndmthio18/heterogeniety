# M0 acceptance tests

## Production-mesh causal tests

Slurm jobs `16330660`--`16330663` used the portable r03 binary on the actual
35,328-cell Greal-81 mesh. All four C/B settings passed.

Key results:

- 960 oriented direct-interface faces; total unique interface area 0.002 m2.
- C0 maximum direct advective flux: exactly 0.
- C0 maximum direct diffusive flux: exactly 0.
- C0 maximum cross-interface non-energy Jacobian row: exactly 0.
- C0 cross-interface thermal Jacobian row: 0.128101, nonzero as required.
- B0 salinity-only Darcy response at fixed pressure: exactly 0.
- B0 temperature-only Darcy response: 1.6172e-16, nonzero.
- B1 reimplementation difference from the upstream law: exactly 0.
- Explicit-filter cross faces: 144, with nonzero advective flow.

The earlier r02 C0 audit was retained as a failed *test-definition* attempt:
it incorrectly required the full Jacobian block to vanish and thereby counted
the deliberately retained heat-conduction derivative as a failure. No solver
physics changed in r03; the audit now separates conservation-equation rows.

## Paired 24 h recovery

The immutable original/patched pair is Slurm `16330674/16330675`. Both use the
same input hash and mesh. Acceptance requires 93,600 s total time, compatible
full-state dimensions, maximum component-scaled state difference <=1e-7, and
the same tolerance over matched water, material, thermal, film, mineral,
native-flux and compact depth-profile histories. This section remains pending
until both jobs finish; M1 is mechanically locked meanwhile.
