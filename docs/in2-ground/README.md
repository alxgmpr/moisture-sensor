# In2 ground conversion and routing handoff

Antenna correction: the extra right-hand keepout described historically below
was incorrect and has been removed. See the current zone-simplification record;
Figure 11's lower ≥15 mm dimension is not a second hatched copper exclusion.

Superseded in zone geometry/counts and routing status by the
[current zone simplification](../zone-simplification/README.md).

The PCB is saved and refilled. In1 retains the name `GND`; In2 is renamed from
`PWR-SHLD` to `GND-SHLD`. Its electronics pour is now `ZoneB_GND_IN2` on GND.
The ground boundary extends under the non-antenna module area and down to
absolute y=104.5 mm. The probe retains its existing driven shield. No non-ground
routes remain on either inner layer; three existing GND segments remain on In1.

## Completed before routing handoff

- Replaced plane-dependent +3V3 distribution with a 0.4 mm B.Cu trunk from the
  PMIC output to the module supply and branches to the pull-ups, programming
  header and humidity-sensor feed. Existing short load escapes retain their
  previous widths. All +3V3 pads are connected in the final refill.
- Moved the raw-battery route from In2 to F.Cu and removed its two obsolete vias.
- Rerouted VBAT on B.Cu, using a short F.Cu PMIC-interrupt crossover to avoid
  crossing the battery route on the same layer.
- Moved the local reset route from In2 to the outer layers, adding a via at
  (92.4,59.3) to pass the existing sensor signal route.
- Preserved all footprints, board outline, antenna keepouts, probe shield and
  electrode polygons/filled copper, schematic, net classes and custom rules.

Routing stopped when Alex offered to finish it. No additional signal routing
or stitching was added after that message; the already-completed work passed
DRC and was retained. Existing through-ground vias connect both inner planes.
Add ground return vias near signal-layer transitions during final routing,
especially around the left I2C transitions and PMIC crossover; a comprehensive
post-route stitching pass has not been completed.

## Validation

Final refill and schematic-parity DRC: **11 existing missing connections,
17 existing warnings, zero other DRC errors and zero schematic-parity issues.**
Baseline had 14 missing connections and the same 17 warning categories/counts.
There are no new clearance, short, keepout, dangling-via or width violations.
All zone outlines are valid and no copper pours overlap on a common layer.
Filled copper is excluded from both antenna rule areas. The original two
net-class regression failures documented in the previous cleanup are unchanged;
net-class corrections remain a separate review.

[Layer preview](layers.png) · [Machine-readable DRC](drc.json).

## Connections left to route

Coordinates are absolute board coordinates in mm. DRC selects representative
endpoints for each disconnected island; these are not necessarily the best
routing attachment points. Preserve the module crystal routes and sensing
shields; keep In2 clear of signal/power tracks to retain its reference function.

1. Pad 4 [/P2.07_SWO] of U1 on F.Cu (81.4970, 44.4500) → Pad 2 [/P2.07_SWO] of R34 on F.Cu (91.5100, 67.8000)
2. Pad 2 [/SWD_RST] of R1 on F.Cu (85.0100, 55.5000) → Track [/SWD_RST] on F.Cu, length 2.0640 mm (85.0405, 58.7250)
3. Pad 1 [/NRESET] of C13 on F.Cu (82.8000, 56.9800) → Pad 1 [/NRESET] of R1 on F.Cu (83.9900, 55.5000)
4. Pad 1 [/NRESET] of R1 on F.Cu (83.9900, 55.5000) → Pad 7 [/NRESET] of U1 on F.Cu (81.4970, 46.7000)
5. Pad 2 [/SCL] of R23 on F.Cu (69.5975, 61.0000) → Track [/SCL] on B.Cu, length 3.1070 mm (72.1970, 68.8030)
6. Pad 2 [/SCL] of R23 on F.Cu (69.5975, 61.0000) → Pad 35 [/SCL] of U1 on F.Cu (72.5030, 48.2000)
7. Pad 2 [/SDA] of R22 on F.Cu (69.5975, 60.0000) → Track [/SDA] on B.Cu, length 2.4042 mm (71.1000, 68.5000)
8. Pad 28 [/SDA] of U1 on F.Cu (72.5030, 53.4500) → Pad 2 [/SDA] of R22 on F.Cu (69.5975, 60.0000)
9. Pad 2 [/SWDIO] of R32 on F.Cu (79.7900, 64.0000) → Pad 5 [/SWDIO] of U1 on F.Cu (81.4970, 45.2000)
10. Pad 2 [/SWDCLK] of R33 on F.Cu (79.7900, 66.5000) → Pad 6 [/SWDCLK] of U1 on F.Cu (81.4970, 45.9500)
11. Pad 17 [/PMIC_INT] of U1 on F.Cu (80.7500, 53.5000) → Track [/PMIC_INT] on B.Cu, length 26.3750 mm (80.3000, 87.7750)

## Recovery

The start-of-task PCB, project, schematic and rule file are together in
`tmp/in2-ground/baseline/`. The final geometric checks are in
`tmp/in2-ground/verify.py`. Do not regenerate from historical routing helpers.
This board remains a routing handoff, not a fabrication release.
