# Simplified zones

The user's latest edited board was used as the baseline. The board is saved
and refilled with **11 zones, down from 15**. No tracks, vias, footprints,
board drawings, schematic or project net-class settings changed.

| Zone | Layers | Purpose |
|---|---|---|
| GND | F.Cu, B.Cu, In2.Cu | One electronics rectangle, x60..93.6, y39.975..106.7 |
| GND_Inner | In1.Cu | Electronics ground extending to y113.6, with the sensing escape notched out |
| SHLD_Front | F.Cu | One stepped shield with explicit electrode cutouts |
| SHLD | B.Cu, In2.Cu | One stepped shield, continuous beneath the electrodes |
| SENSE1_electrode | F.Cu | Unchanged electrode rectangle |
| SENSE2_electrode | F.Cu | Unchanged electrode rectangle |
| BL54L15_AntennaKeepout | All copper | One exclusion following the hatched antenna region |
| NoCopperSHT45 | All copper | Sensor core; also selects the custom no-track rule |
| SHT45_Jut | All copper | Larger no-fill/no-via thermal-isolation area |
| ESD_SENSE1 | F.Cu | Local clamp clearance exception |
| ESD_SENSE2 | F.Cu | Restored local D9 clamp clearance exception |

The separate ground and shield layer groups are necessary: In1 must retain
clamp-ground coverage where the other layers carry the driven shield, and the
front shield needs electrode cutouts while the inner/bottom shield does not.
The sensor's two exclusions likewise have different track restrictions.

## Simplification and corrections

Merged the two front shield sections and the two inner/bottom shield sections.
Their tops now start at y107.1, with the main ground rectangle ending at y106.7.
This straight boundary preserves ground to U3's digital-side ground pad without
splitting its supply return. Main ground and shield pours use solid connections;
this removes the six starved-thermal errors present in the edited baseline.
Electrode dimensions and existing electrode connection settings are unchanged.
The front shield retains the user's 0.5 mm local clearance; inner/bottom shield
retains 0.25 mm. Electrical sense/shield clearance rules remain active.

Removed four obsolete FinePitchFanout areas and their two now-unused rule
selectors. A trial DRC with all four areas removed produced the same findings
as with them present. Restored ESD_SENSE2 to the local D9 rectangle already named
by the existing clamp rule; this resolves its 0.4 mm package-gap violation
without weakening the general sense-to-ground rule.

The antenna keepout is x57..80.5, y39..45 with the existing pad-39 notch.
The extra right-hand exclusion and off-board connecting bridge have been
removed after rechecking Figure 11. The lower ≥15 mm dimension was incorrectly
interpreted as a second copper exclusion; that area is not hatched. Ground now
fills the right-hand area, including the ground-land strip. The actual antenna
keepout still bans tracks, vias, pads and fills on every copper layer.

## Verification

- All zone polygons are valid; copper pours do not overlap on shared layers.
- No filled copper intersects the combined antenna exclusion. The ground-land
  strip is outside it, and the hatched antenna region is covered.
- Refill/DRC: **19 existing missing connections, 26 warnings, zero other errors,
  zero schematic-parity issues.** Baseline had the same missing-connection count
  and warning categories, plus six thermal errors and one clearance error.
- No routing was performed. The 19 connections remain for the user's routing.
- Repository checks: 37 pass; the same two existing net-class tests fail.
  The antenna test now expects one antenna keepout.
- All four copper-layer plots were visually reviewed.

[Layer preview](layers.png) · [DRC report](drc.json).

A complete pre-change snapshot is in `tmp/zone-simplify/baseline/`; geometric
verification is in `tmp/zone-simplify/verify.py`. This supersedes earlier zone
counts and ground boundaries in the prior cleanup and In2 conversion reports.
