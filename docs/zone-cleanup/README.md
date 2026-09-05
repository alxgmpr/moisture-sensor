# Pour and keepout cleanup — 2026-09-04

Antenna correction: the extra right-hand keepout described historically below
was incorrect and has been removed. See the current zone-simplification record;
Figure 11's lower ≥15 mm dimension is not a second hatched copper exclusion.

Superseded in zone geometry/counts and routing status by the
[current zone simplification](../zone-simplification/README.md).

The maintained PCB is updated and refilled. The subsequent
[In2 ground conversion](../in2-ground/README.md) supersedes the power-plane
architecture and DRC counts recorded below. This is a polygon cleanup, not a
routing completion or fabrication release. Source: user-supplied
`/Users/alex/Downloads/453-00001R_new.pdf`, sections 7.2–7.3 (pages 21–22) and
Figure 11 / section 8.2 (page 25). The relevant PDF pages were rendered and
visually inspected.

## Changes

- Front shield now has explicit electrode cutouts with the existing 0.2 mm
  sense-to-shield spacing. The electrode polygons and their filled copper are
  unchanged. There is no longer a shield polygon painted beneath each electrode.
- Front and inner/bottom main shield boundaries abut their escape zones without
  overlapping. Separate zones retain the existing thermal-versus-solid pad
  connections and local clearances; merging those settings would alter behavior.
- `SenseNoGround` is merged into `ProbeNoGround` as one continuous In1 pour
  exclusion with the same prohibited features. No named custom rule referred
  to the removed area.
- `ZoneB_GND_IN1` follows the antenna and sense exclusions directly. Its
  actual filled copper is unchanged, including the ground strip to U1 pad 1.
- The right antenna keepout extends to x97, showing the full ≥15 mm extension
  beyond the module's x82 edge. The fixed host edge is x94, so this changes no
  host copper. Corrected the earlier 5 mm description in the layout and module
  notes. The left extension remains x57; both areas cover all four copper layers
  and prohibit tracks, vias, pads and zone fills.

The manufacturer's land-row strip and existing 0.026 mm ground-pad-39 notch
remain. The notch accommodates the manufacturer's land dimensions at the
nominal keepout boundary; it is not a general routing exemption. The supplied
figure also permits adapting land dimensions to the assembly process.

## Intentional rule-area overlays

`FinePitchFanout` and the two ESD areas select local custom rules, so their
presence over copper is intentional. They are not copper pours. The SHT45 core
rule area remains nested in the larger jut exclusion: the jut prohibits fills
and vias, while the core's named custom rule additionally prohibits tracks.
These areas have distinct scopes and should not be merged into a blanket
track ban over the sensor connections. No custom clearance or width rule was
relaxed.

## Verification

- All zone polygons are valid; no copper-pour outlines overlap on a shared layer.
- No filled copper intersects either all-layer antenna keepout.
- Footprints, pads, tracks, vias and board drawings are unchanged from the
  start-of-task snapshot. The three vias beneath the module body remain tented
  on both sides. No new ground-pad missing connection is reported.
- Actual re-filled ground, power, both electrodes and inner/bottom shield copper
  match the baseline geometrically. Front shield symmetric difference is
  0.0936494 mm², localized to cutout/boundary cleanup; its net area falls by
  approximately 0.09312 mm².
- Final DRC is identical to baseline by finding type, severity and item UUID:
  **14 existing missing connections, 17 existing warnings, zero other DRC
  errors and zero schematic-parity issues.** Warnings: 11 library-footprint
  differences, 4 dangling tracks, 1 silk overlap and 1 silk-over-copper.
- Repository tests: **37 passed, 2 failed**. Both failures also reproduce using
  the untouched baseline project. The project still contains the legacy RF
  net class / retired net patterns and lacks the complete assignments expected
  by `tests/test_pcb_routing_rules.py`. Net classes were not changed here;
  correcting assignments needs a separate clearance/refill review, especially
  for the protected sense and programming nets.

The antenna copper geometry is checked against the supplied specification.
Enclosure compliance is not established: the existing holder/enclosure spacing
still falls short of some of the manufacturer's 30/40 mm metal-separation
recommendations. Keep antenna hardware nonmetallic and qualify the assembled
product's RF performance.

## Review and recovery

[Four-layer copper review](layers.png).

The start-of-task board is `tmp/zone-cleanup/before.kicad_pcb`. A complete
PCB/project/schematic/rules snapshot is in `tmp/zone-cleanup/baseline/`.
Before/after DRC reports are in `tmp/zone-cleanup/before-drc.json` and
`tmp/zone-cleanup/after-drc.json`; geometric validation is in
`tmp/zone-cleanup/verify.py`. The baseline directory's auxiliary DRC report has
extra library-resolution warnings because its relative library paths differ;
the authoritative before/after DRC reports were both run at the project root.
