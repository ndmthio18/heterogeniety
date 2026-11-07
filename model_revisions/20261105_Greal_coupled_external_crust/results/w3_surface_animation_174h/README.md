# W3 surface salt-deposition animation

This animation shows the model-derived equivalent external NaCl-crust height on the 384 native W3 atmospheric top faces from 0 to 174 h. It does not show an experimentally observed crystal morphology.

- Source: completed Frodo 174 h coupled external-crust run.
- Variable: accepted equilibrium solid NaCl inventory, reinterpreted as external inventory.
- Height: `solid_vf * cell_volume / top_face_area / (1 - 0.43)`.
- Time sampling: every 2 h from the hourly VTU series.
- Spatial rendering: piecewise constant native top faces; no interpolation or smoothing.
- Geometry rendering: salt-bearing faces are extruded from the sand surface; side faces use directional darkening only to reveal shape, while the quantitative color scale applies to the top-face height.
- Display: fixed 0–0.42 mm color scale; 3D vertical display scale is exaggerated for visibility.
- Detection threshold: solid volume fraction > 1e-12.
- First accepted solver solid: 71.917 h.
- Final W3 external mass: 159.642887 mg.
- Final maximum equivalent height: 0.390557 mm.
- Final crust-bearing area: 542.412560 mm2.

The raw extracted values, native face geometry, reconstruction QA, and hashes accompany the media files.
