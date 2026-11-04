# G-real geometry audit

- Mesh: unchanged 50 mm cylinder with 40 mm split sand and 4.5 mm explicit filter.
- Cells: 35,328 total; 4,608 filter cells; six 0.75 mm filter layers.
- Lower boundary topology: 768 faces, all registered.
- Port: centered 4.000 mm nominal circle, exact polygon/circle overlap fractions.
- Analytical and integrated area: `1.2566370614359173e-5 m2` (relative difference `6.66e-16`).
- Active lower faces: 64, all partial/cut faces.
- Port-map SHA256: `d30db051344d4d900820a9834c71425a2910a1111f1b7f6aa0c9a32648bd4d15`.
- Filter-mesh SHA256: `4a47ac0b67c6bca83b7d1241558346a66d7eb830642b923ee9005f554de86395`.

The maximum equivalent lower-face diameter is 2.496 mm. The opening is therefore only about 1.6 such diameters across. Area conservation and boundary registration pass, but radial pressure/spreading convergence does **not**. A targeted local radial refinement is still required before making mesh-independent statements about near-port flow. The six-layer filter resolves thickness at 0.75 mm vertically; a controlled 12-layer comparison is required to quantify vertical discretization error.
