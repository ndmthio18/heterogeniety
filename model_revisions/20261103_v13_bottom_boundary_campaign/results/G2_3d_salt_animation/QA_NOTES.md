# G2 3D dissolved-NaCl animation — QA notes

## Source integrity

- Case: accepted 3D G2 production result, 174 h evaporation after 2 h pre-equilibration.
- Frame selection: 88 saved states at exactly 2 h evaporation-time spacing from 0 to 174 h; no temporal interpolation.
- Remote source bundle: `G2_2h_animation_fields.tar`, 558,407,680 bytes.
- Bundle SHA256: `b27bc4aa1ff4c059193ba47a84fdc0e3332e5dde22df8790b5d04f47a70c9275`.
- All 88 gzip-field SHA256 values were verified locally against `G2_2h_frame_manifest.json` before rendering.
- Dissolved concentration was calculated cell-wise as `x^NaCl_liq * rhoMolar_liq / 1000` in mol L-1.

## Visual mapping

- Camera, half-cylinder clipping, scalar ranges, color maps, transparency, geometry, and annotations are identical in every frame.
- The left panel uses exact z=0 mesh faces as a high-opacity quantitative section plus transparent cell-threshold layers for 3D context. Its fixed absolute-concentration range is 1.0–5.5 mol L-1. The nominal initial condition is 1.0 mol L-1; the smallest audited sand-cell value is 0.99815 mol L-1 and therefore maps to the lower endpoint.
- The right panel uses the actual F36 mesh layer nearest y=12.5 mm. For each native radial ring, it displays `cell concentration - same-ring mean` with a fixed diverging range of -0.15 to +0.15 mol L-1. This removes the dominant radial background so the lateral instability is visible. Values outside the fixed limits saturate; there is no per-frame rescaling.
- No spatial resampling, smoothing, temporal interpolation, or per-frame normalization was applied. The two panel colors encode different quantities and must not be compared directly.
- The 4.5 mm explicit filter is gray and translucent. The G2 5 mm-diameter supply port is cyan-blue and shown beneath the bottom boundary as a context glyph.
- Cyan wireframes identify cells with non-zero equilibrium solid inventory. They encode location only. The fixed-hydraulics inventory variable is not interpreted as geometric pore occupancy or external crystal morphology.

## Encoded artifacts

- MP4: H.264/yuv420p, 1920 × 1080 px, 8 fps, 112 encoded frames, 14.0 s. The 88 physical frames are unchanged; the additional frames are endpoint holds.
- GIF preview: 800 × 450 px, 88 physical frames, 160 ms per frame, infinite loop.
- MP4 SHA256: `57419b2e544f84ac9bf21d6a5dbb14586ca16344f4265e68dbc58d46feed067e`.
- GIF SHA256: `fb0ff55893fe57d7e7556b489f43b3bcc07cdc188587b6f45dc7aa27f7f8f8cf`.

## Visual inspection

- Inspected source renders at 0, 24, 60, 72, 108, and 174 h.
- Inspected decoded MP4 frames at start, midpoint (96 h), and end; no blank frames, clipping defects, title overlap, or color-bar drift were found.
- The 0 h uniform 1 mol L-1 field and the later low-concentration F36 side remain visible in the exact central section after switching to a brighter truncated sequential color map.
- The F36 panel clearly resolves the red/blue lateral symmetry breaking at 24, 60, 108, and 174 h. The diagnostic is ring-mean relative and therefore cannot be read as absolute concentration.
- The 72 h frame shows the first cyan solid-inventory location in the 2 h sampling. This is a saved model equilibrium event, not an experimental nucleation time.
- At 174 h the audited dissolved concentration statistics are: minimum 1.1641, median 2.3997, 95th percentile 4.9629, maximum 5.3315 mol L-1; 122 cells contain solid inventory.

## Automated preflight

The Python source passed the scientific-figure preflight with 11 PASS, 3 WARN, and 0 FAIL findings. The warnings are accepted for this screen-first animation deliverable:

- no TIFF: the primary artifact is video; the static key-frame plate is available as PNG/PDF/SVG;
- 300 dpi PNG rather than 600 dpi TIFF: used only as a review/contact sheet;
- 304.8 mm contact-sheet width: a five-frame QA plate, not a manuscript single/double-column panel.

## Scientific limitation

The animation visualizes a model prediction. It does not independently validate G2 against MRI, does not establish an experimental crystallization time, and does not represent external efflorescent crust morphology.
