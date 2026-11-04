# G2 3D salt-concentration animation: figure contract

Core conclusion: The accepted G2 simulation predicts how dissolved NaCl redistributes through the coarse/fine cylindrical specimen during 0–174 h evaporation, while the explicit bottom filter and 5 mm supply port remain geometrically identifiable.

Figure archetype: image plate + quantitative spatial field.

Target output: native 4K UHD (3840 x 2160 px), 16:9 scientific animation for screen presentation, a 1600 x 900 px preview GIF, high-resolution key frames, and a machine-readable source manifest. Both color bars occupy dedicated legend gutters outside the specimen and instability data regions.

Backend: Python (PyVista/VTK for all rendering; imageio-ffmpeg for encoding).

Evidence hierarchy:

- Hero evidence: paired fixed-camera views at 2 h intervals. The left panel shows the full-domain absolute concentration on a fixed 1.0–5.5 mol L-1 scale. The right panel shows the native F36 horizontal mesh layer nearest y=12.5 mm as the cell-wise deviation from the mean of cells on the same native radial ring, on a fixed -0.15 to +0.15 mol L-1 scale. This removes the axisymmetric radial background and exposes lateral symmetry breaking without spatial interpolation or per-frame normalization.
- Spatial context: translucent cylindrical wall, coarse/fine split annotation, explicit 4.5 mm bottom filter, and 5 mm supply port.
- Supporting evidence: optional cyan wireframe marking cells with non-zero equilibrium solid inventory; it encodes location only, not crystal volume.

Data and transformation contract:

- Dissolved NaCl concentration: `x^NaCl_liq * rhoMolar_liq / 1000`, in mol L-1.
- Evaporation time: `(simulation_time_s - 7200) / 3600`.
- Frames: all 88 saved states at exactly 2 h spacing from 0 to 174 h; no temporal interpolation.
- Color ranges: full domain fixed at 1.0–5.5 mol L-1; F36 ring-mean anomaly fixed at -0.15 to +0.15 mol L-1 for every frame. Values beyond the anomaly limits are saturated, not rescaled. The two bars are separately labelled and must not be compared by color.
- Geometry: model coordinates and dimensions are preserved; the front half is clipped only for visibility.

Image-integrity notes:

- Opacity and clipping are identical for every frame within each view. In the full-domain panel, the exact z=0 mesh faces form the higher-opacity quantitative section and the surrounding mesh remains translucent. The F36 panel uses one actual horizontal cell layer with no interpolation.
- No smoothing, spatial interpolation between mesh cells, temporal interpolation, or per-frame color rescaling is used for the quantitative cut surface.
- The fixed-hydraulics solid variable is an equivalent inventory quantity. Any solid overlay marks affected cells only and must not be interpreted as pore occupancy, external efflorescent crust, or crystal morphology.

Reviewer risks:

- A 3D volume view can conceal internal gradients; the fixed half-cylinder cutaway and fixed camera mitigate this.
- Transparency is qualitative. Quantitative values must be read from the fixed color bars and the traceable source fields. The F36 anomaly is a diagnostic of lateral departure from ring symmetry, not an absolute concentration field.
- This is a model visualization, not independent validation against MRI and not evidence for experimental crystallization onset.
