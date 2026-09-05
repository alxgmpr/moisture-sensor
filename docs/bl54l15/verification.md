# Verification — BL54L15 routing handoff

Checked 2026-09-04 using KiCad CLI 10.99, file format 20260828, with the
repository's existing ERC/DRC configuration. Zones were refilled and saved
before checking and exporting. No new rule exclusions were added to hide
violations. This is a routing handoff at Alex's request, **not a fabrication
release**. No boards or components were ordered.

## Check results

| Check | Snapshot before migration | BL54L15 handoff |
|---|---:|---:|
| ERC errors | 0 | **0** |
| ERC warnings | 24 | **11** |
| Physical DRC errors | 13: 9 width, 4 clearance | **0** |
| Unconnected items (DRC errors) | 6 | **15**, deliberate routing handoff |
| PCB warnings | 49 | **18** |
| Schematic/PCB parity differences | 0 | **0** |
| Repository tests | — | **34 passed** |

Reports: [ERC](erc.json), [DRC with each missing endpoint](drc.json),
[baseline ERC](baseline-erc.json), [baseline DRC](baseline-drc.json),
[test output](tests.txt), [preservation checks](preservation.json).
Earlier audit/checklist counts refer to different intermediate board states;
the baseline above was taken from the actual dirty working tree immediately
before this migration.

All 11 ERC warnings are retained library-symbol differences (C3, C13,
C21–C28 and U2), present in the baseline. The tiny dangling schematic wire and
its orphan label were removed. Current PCB warnings comprise 11 retained
footprint-library differences, the preexisting R22/R23 silkscreen clearance,
and six newly exposed dangling route anchors from disconnecting the old MCU
fanout, intentionally retained for hand routing. New
module silkscreen clipping/overlap warnings were resolved. There are no new
physical DRC errors; the outstanding error category is unrouted connections.

The project already disables missing courtyard, off-center track/via,
tuning-profile geometry, footprint-filter and footprint-type checks. ERC also
has its preexisting single-global-label, four-way-junction, simulation and
footprint-filter checks disabled. These settings are listed in the JSON
reports and were preserved; a zero error count is under those project rules.
U1 itself has a courtyard and its LGA land pattern is explicitly checked.

## Connectivity and preservation

- Verified every used U1 pad against the Ezurio pin table: 26 VDD;
  1/16/27/39 GND; 25/24 XL1/XL2; 35/28 SCL/SDA; 17 PMIC_INT;
  4 SWO; 5/6 SWDIO/SWDCLK; 7 nRESET. Other 25 module GPIO pads are NC.
- Preserved all firmware GPIO assignments and reset/programming topology.
- Netlist comparison removes only the retired parts and replaced U1 from each
  snapshot, then compares complete remaining node groups: **26 groups identical**.
- **19 retained footprint placements** and **all 40 outline primitives** match
  the starting PCB. Only U1, C3, X1, R1 and C13 were replaced/repositioned.
- Current netlist fingerprint has **51 entries**, including explicit NC pins.
  Obsolete RF, DCC/DECD/DECA and XC1/XC2 nets are absent.
- Tests check all 39 land centers, pad size/layers, assigned signal pads,
  deletion of obsolete components, four-layer antenna rule areas, JLC exclusion,
  separate paste stages, full-product DigiKey metadata, and retained project
  power/sensing/routing/model/generator-safety invariants.

## Visual inspection

Inspected actual KiCad-generated front copper and all three other copper layers
around U1: no host copper in the antenna rule areas, continuous In1 ground under
the electronics and pin-1 land strip, nearby ground vias, local X1/C3 wiring and
no new courtyard/clearance violations. Reviewed module pin labels, common GND
connection, external-support notes, DNP assembly-stage note and the updated
schematic drawing. The module body/keepout annotation in the placement image is
derived from the actual board geometry; the underlying copper is KiCad output.

- [Annotated final placement](placement.png)
- [Front mask — only intended lands exposed under U1](F_Mask.png)
- [Front copper](F_Cu.png), [In1 ground](GND.png), [In2 power](PWR-SHLD.png), [back copper](B_Cu.png)
- [Schematic module detail](schematic-module.png)

The footprint's 3D model is a nominal 14 × 10 × 1.6 mm envelope, not detailed
vendor geometry. Enclosure RF performance and thermal process cannot be
established from these drawings. Existing SHT45/holder positions and enclosure
outline were preserved; no physical assembly was performed.

## Remaining work

Finish the 15 connections and remove unused route anchors. Refill and require
zero unconnected items; reconcile library warnings and R22/R23 silk before fab.
Qualify the module supply's 10 mV noise/ripple limit, total effective converter
load capacitance, X1/HFXO trim/startup, timed System OFF wake, and hot-air LGA
attachment. The fixed battery/enclosure geometry does not meet all preferred
manufacturer metal-separation distances; closed-enclosure radiated testing or
a mechanical revision remains necessary. C23 bias and C26/C27/C28 order codes,
plus exact BT1 assembly sourcing, are retained open BOM issues.

The review manufacturing output is regenerated by
[tools_export_bl54l15.py](../../tools_export_bl54l15.py), with source hashes in
`production/bl54l15-routing-review/source-sha256.json`. U1 is included in the
20-component product BOM, excluded from the 19-placement JLC BOM/CPL and JLC
paste, and present as 39 apertures in the separate manual-paste stage.

## Current unconnected endpoints

| From | To |
|---|---|
| Pad 1 [/NRESET] of C13 on F.Cu (82.800, 56.980 mm) | Pad 1 [/NRESET] of R1 on F.Cu (83.990, 55.500 mm) |
| Pad 1 [/NRESET] of R1 on F.Cu (83.990, 55.500 mm) | Pad 7 [/NRESET] of U1 on F.Cu (81.497, 46.700 mm) |
| Pad 2 [/SWD_RST] of R1 on F.Cu (85.010, 55.500 mm) | Track [/SWD_RST] on F.Cu, length 2.0640 mm (85.040, 58.725 mm) |
| Pad 1 [+3V3] of R22 on F.Cu (68.403, 60.000 mm) | Pad 1 [+3V3] of R23 on F.Cu (68.403, 61.000 mm) |
| Pad 1 [+3V3] of R22 on F.Cu (68.403, 60.000 mm) | Track [+3V3] on F.Cu, length 2.9345 mm (74.000, 54.425 mm) |
| Pad 1 [+3V3] of R23 on F.Cu (68.403, 61.000 mm) | Track [+3V3] on F.Cu, length 1.3975 mm (67.832, 68.200 mm) |
| Via [+3V3] on F.Cu - B.Cu (91.800, 63.282 mm) | Pad 1 [+3V3] of J4 on F.Cu (84.665, 62.760 mm) |
| Pad 2 [/SCL] of R23 on F.Cu (69.597, 61.000 mm) | Track [/SCL] on B.Cu, length 3.1070 mm (72.197, 68.803 mm) |
| Pad 2 [/SCL] of R23 on F.Cu (69.597, 61.000 mm) | Pad 35 [/SCL] of U1 on F.Cu (72.503, 48.200 mm) |
| Pad 2 [/SDA] of R22 on F.Cu (69.597, 60.000 mm) | Track [/SDA] on B.Cu, length 2.4042 mm (71.100, 68.500 mm) |
| Pad 28 [/SDA] of U1 on F.Cu (72.503, 53.450 mm) | Pad 2 [/SDA] of R22 on F.Cu (69.597, 60.000 mm) |
| Pad 5 [/SWDIO] of U1 on F.Cu (81.497, 45.200 mm) | Pad 2 [/SWDIO] of J4 on F.Cu (84.665, 64.030 mm) |
| Pad 6 [/SWDCLK] of U1 on F.Cu (81.497, 45.950 mm) | Pad 4 [/SWDCLK] of J4 on F.Cu (84.665, 66.570 mm) |
| Pad 4 [/P2.07_SWO] of U1 on F.Cu (81.497, 44.450 mm) | Pad 6 [/P2.07_SWO] of J4 on F.Cu (85.935, 67.840 mm) |
| Track [/PMIC_INT] on B.Cu, length 26.3750 mm (80.300, 87.775 mm) | Pad 17 [/PMIC_INT] of U1 on F.Cu (80.750, 53.500 mm) |
