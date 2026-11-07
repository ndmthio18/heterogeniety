# GitHub delivery policy

This revision is published as a lightweight, auditable scientific delivery.

Included:

- Coupled DuMuX source overlays and application source.
- Runtime input and feature configuration.
- C++ constitutive test and Python launch/analysis scripts.
- Build, launch and source-hash metadata.
- Compact accepted-step budgets and derived comparison tables.
- Reports, PDF/PNG figures and the small W3 surface animation products.

Excluded:

- Solver executables and shared-library payloads.
- Raw VTU/PVD field series.
- Duplicate snapshot and source tar archives.
- Python bytecode caches.

The excluded artifacts remain identified by the recorded source/input/executable hashes and remote paths. Their absence from Git does not convert partial reports into complete full-field verification.
