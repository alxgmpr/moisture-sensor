# Leafy sprout front silkscreen

Approved source: `../front-graphic-concepts/sprout.png`.

Added through the running KiCad editor's IPC API as a single group named
`Leafy sprout radio artwork` on F.SilkS. The artwork occupies x=70–84 mm,
y=119–137 mm (14 × 18 mm), centered on the upper probe above the soil line.
Dark source pixels become silkscreen ink; white areas remain clear.

The source was cropped, sampled onto a 56 × 72 grid, thresholded, and converted
to filled rectangles with a 0.25 mm grid pitch. This preserves pixel steps and
removes raster antialiasing. `ink-mask.png` records that grid;
`add_sprout.py` records the IPC placement, and `artwork-items.json` records IDs.

Verification:

- All pre-existing board objects are structurally unchanged.
- DRC before and after: 40 existing violations, zero unconnected items.
- No DRC violation involves the new artwork. An existing silk clearance report
  for the same two existing IDs changed its reported distance slightly.
- Visually reviewed `after.svg` / `after.png`: artwork clears the board edges,
  exposed pads, and existing markings.

This updates the board source, not previously exported fabrication packages.
