# Research plan

## Causal estimands

The primary surface estimand is

`Delta_conn(B,t) = M_W3,0-3mm(C1,B,t) - M_W3,0-3mm(C0,B,t)`.

The interaction is

`Delta_int(t) = Delta_conn(B1,t) - Delta_conn(B0,t)`.

These are model-internal counterfactual contrasts. They are not independent
experimental validation. C0 removes only direct sand-interface mass exchange;
the shared filter and thermal conduction remain.

## Stages

1. **M0:** production-mesh switch tests and original/patched C1B1 24 h
   recovery.
2. **M1:** C1B1, C0B1, C1B0 and C0B0 to 60 h evaporation plus 2 h
   pre-equilibration.
3. **M2:** conservative F36/W3/filter and depth-band pathway decomposition,
   separating gross positive, gross negative and net transport.
4. **M3:** conditional 3x3 screen with coarse-permeability factors
   0.5/1/2 and gas-film factors 0.75/1/1.33. Center C1B1/C0B1 cases reuse
   M1, leaving 16 additional B1 cases. B0 corner extensions are prepared but
   will be released only after the B1 response surface is inspected.
5. **M4:** filter-permeability endpoints 3.39e-12 and 7.64e-12 m2 at the
   baseline sand and film settings.

## Candidate coordinates and evidence boundary

The initial coordinates are `Ra_c`, `Pe_E`, their ratio, permeability contrast
and a reference lateral hydraulic-to-evaporative velocity ratio. Reference
density and evaporation scales will be evaluated consistently from the
Greal-81 thermodynamics and initial boundary state before M3 release. Because
changing coarse permeability also changes contrast and relative filter
resistance, the screen cannot identify a universal two-parameter law.

No discrete regime, sign reversal or transition curve is assumed. A
continuous response surface will be retained if classifications are not
supported. Precipitation events, minimum saturation, numerical failures and
near-zero normalization denominators are explicit validity flags.
