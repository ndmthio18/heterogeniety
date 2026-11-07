# Physically scaled Cartesian 2D model

## Evidence boundary

This is a dimensional reduction for mechanism screening, not an axisymmetric
surrogate and not an exact representation of the cylindrical radial flow
field. Agreement in integrated fluxes or response signs will not establish
three-dimensional validation.

## Primary geometry

For cylinder radius `R=0.025 m` and sand height `H=0.04 m`,

```text
W2D = pi R / 2 = 0.039269908169872414 m
b   = 2 R      = 0.05 m
```

so that

```text
W2D H b = pi R^2 H = 7.853981633974484e-5 m3
W2D b   = pi R^2   = 1.963495408493621e-3 m2
H b     = 2 R H    = 2.000000000000000e-3 m2.
```

The two materials each occupy `W2D/2 = 19.634954 mm`. Every finite-volume
storage and face flux is multiplied by the physical extrusion `b`. The exact
3D Greal-81 vertical levels are retained; the upper cell is about 0.0667 mm.
The grid has 4080 sand cells (4692 including the six-layer filter).

The 50 mm-wide sensitivity keeps volume and top area by using
`b=pi R^2/0.05=39.269908 mm`; its interface area is only 0.001570796 m2 and is
therefore not geometrically equivalent in all three measures.

## Bottom supply

- **A, mechanism control:** no explicit filter; the full bottom is a
  pressure-controlled 1 M reservoir at the Greal-81 head.
- **B, primary comparison:** a 4.5 mm P3 filter (`K=5.30e-12 m2`) shared by
  both materials. The 4 mm circular 3D inlet area is conserved as
  `w=A_circle/b=0.251327412 mm`. Exact inlet edges are mesh nodes. A 4 mm 2D
  slot is explicitly excluded.

Configuration B preserves inlet area, not the three-dimensional radial
spreading resistance. Configuration A/B comparison is therefore a robustness
test, not a calibration.

## Physics and causal controls

The source retains Greal-81 nonisothermal two-phase/component transport,
Pitzer water activity, concentration-dependent fluid properties, local film
evaporation, equilibrium NaCl precipitation and fixed hydraulic porosity and
permeability. The film thickness is fixed at `8.100162249880822 mm`; the 3D
polygon-area correction is set to one because the extruded top area is already
the exact nominal cylinder area.

`InterfaceExchangeEnabled=false` zeros direct F36/W3 advective and molecular
diffusive component fluxes in the assembled residual while retaining thermal
conduction and shared-filter communication. `SalinityBuoyancyScale=0` removes
only the salinity density anomaly from gravity terms; temperature response,
gravity, viscosity and constitutive properties remain.

The 2D vertical side faces do not reconstruct the full cylindrical wall or
front/back radial heat field. This limitation must be tested against early 3D
integral responses before the screen is interpreted physically.
