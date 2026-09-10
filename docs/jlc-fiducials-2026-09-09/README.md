# JLCPCB Economic assembly alignment features

Superseded in part: the user subsequently requested removal of all copper fiducials. See [removal record](../jlc-fiducial-removal-2026-09-09/README.md). The three tooling holes remain.

Updated the maintained board and schematic for JLCPCB's [tooling-hole requirements](https://jlcpcb.com/help/article/how-to-add-tooling-holes-for-pcb-assembly-order) and [fiducial guidelines](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order).

- FID1–FID4: 1 mm circular copper pads, 2 mm mask openings, 0.6 mm copper clearance, no paste. Three schematic-linked footprint fields updated; FID4 remains board-only.
- Repositioned fiducials clear of components and the antenna keepout. Minimum clearance from the 1.1 mm-radius copper keepout to the exterior board outline is 3.4167 mm, exceeding JLC's 3.35 mm minimum. See `edge-clearances.json`.
- TH1–TH3: 1.152 mm round NPTH, 0.148 mm mask expansion on both sides (1.448 mm openings). Located at the upper left, upper right, and clear tip below the sensing electrodes. Reusable footprint: `lib/footprints.pretty/ToolingHole_JLC_1.152mm.kicad_mod`.
- Removed five nearby GND stitching vias to clear the new features. Tracks, track arcs, board outline, and all zone outlines remain identical to the pre-change snapshot. Zones refilled. Coordinates are in `placement.json`.
- All alignment features are excluded from BOM and placement files.

Validation: native KiCad DRC and schematic parity found zero unconnected items and zero parity issues. The same two pre-existing +3V3-via keepout errors and 38 warnings remain; violation identities match the baseline. These two errors are already documented as accepted in `tools_export_jlc_economic.py`. ERC had no errors. Three alignment-feature regression tests and two quote-archive tests pass.

Regenerated `production/jlc-economic-quote/` using `python3 tools_export_jlc_economic.py`. The NPTH drill file contains exactly three hits using its 1.152 mm tool. Front-mask Gerber contains the 1.448 mm tooling openings and 2 mm fiducial openings. Rendered and inspected copper and mask Gerbers. BOM and CPL agree at 38 fitted components / 21 BOM rows. No order was placed.
