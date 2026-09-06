# nRF Moisture Sensor — design review, 2026-09-05

The existing 0.4/0.5 mm 3V3 traces have ample modeled current capacity for this board. The significant unresolved power issues are effective capacitance, CR2032 droop, PMIC mode/power limits and radio supply ripple. I²C uses the correct module pads. A smaller outline is feasible to explore, but the proposed lower-right module location cannot simply replace the present placement without mechanical/RF changes.

## Work completed

| Task | Result |
|---|---|
| Sweep checkpoint before edits | `0a7771b`; design, libraries, scripts and review records preserved; scratch/caches omitted |
| Rename | KiCad project/schematic/PCB/rules now `nrf-moisture-sensor`; displayed title **nRF Moisture Sensor**; current tools and tests updated |
| Copper/current review | [Actual widths, polygons, vias, stackup, reproducible sweeps and bench procedure](../power-review-2026-09-05/README.md) |
| Module pins and capacitor review | [Exact pin mapping, capacitor inventory, manufacturer evidence](../component-review-2026-09-05/README.md) |
| Schematic readability | [A2 schematic PDF](../schematic-review-2026-09-05/nrf-moisture-sensor-schematic.pdf), section labels, corrected PMIC graphics; electrical netlist unchanged |
| Shrink assessment | [30 mm trim feasibility](shrink-feasibility.md) and [dimensioned concept](shrink-concept.png); live outline and module placement retained |
| BOM synchronization | [BOM.md](../../BOM.md) regenerated from [KiCad-exported source fields](product-bom.csv) |
| Final verification | Zero DRC errors, zero unconnected items, zero schematic parity issues; zero ERC errors; 43 tests and 261 subtests pass |

The repository directory remains `/Users/alex/moisture-sensor-carrier` so the active workspace and existing local integrations continue to resolve. Open `nrf-moisture-sensor.kicad_pro` for future editing. Old root fabrication outputs were moved to `tmp/pre-rename-fabrication`; historical reports/backups retain their original names. No fabrication package was released.

## Findings that affect the design

- **3V3:** actual outer-layer traces are 0.4/0.5 mm on 35 µm copper. IPC-2221 screening gives approximately 1.23/1.45 A at a 10°C temperature rise; deliberately reduced geometry gives 0.89/1.05 A. These are model results, not certified board ratings. The long SHT branch is approximately 4.1–7.5 mV at 100 mA, excluding trunk, return and supply droop.
- **Stackup:** modeled from the board's 35/15.2/15.2/35 µm copper. JLC's standard four-layer designation does not uniquely determine dielectric construction; confirm the selected stack when ordering.
- **I²C:** U1.35 is P1.11/SCL and U1.28 is P1.10/SDA. This is valid for TWIM22. Module land numbering does not imply fixed adjacent pairs; no pin swap is needed.
- **C21:** current 10 µF 0402 selection has insufficient demonstrated DC-bias margin against the 3.5 µF effective minimum. Typical curve plus tolerance screening gives about 3.2 µF at fresh-cell voltage. Qualify or revise it before release.
- **C23:** the exact 22 µF VINT capacitor's worst-case biased value remains unqualified. Obtain the exact manufacturer curve/model and include tolerance, temperature and aging.
- **VOUT:** C3+C25+C27 are 12.3 µF nominal, 14.75 µF at positive production tolerances before bias, temperature and module loading. The effective upper limit is 15 µF. C26/C28 belong to the LDOSW branch from VINT and must not be directly added to VOUT.
- **Peak loads:** nPM2100's 450 mW limit corresponds to about 136 mA at 3.3 V under its specified conditions. The SHT45 heater alone can require 100 mA; stagger radio/heater operation and characterize the real battery. Bulk bypass cannot sustain its 100 ms–1 s heater pulse.
- **Radio:** validate ≤10 mV ripple at the module. HP-mode scheduling and transient behavior need prototype measurements; width calculations cannot establish this.
- **Size:** cutting at Y=70 mm would reduce overall length from 155 to 125 mm. The examined lower-right module placement conflicts with battery-terminal antenna clearance and leaves only 0.2 mm to the mounting-hole edge. A coupled placement/enclosure redesign is required.

## Board cleanup and rule rationale

1. Connected isolated J4 ground pad 3 with a 0.2 mm local trace and 0.5/0.2 mm via; refill verifies connectivity.
2. Removed the overlap between GND via-stitching generator regions while preserving every existing generated via. Future generator areas are disjoint.
3. Renamed the extra board-only fiducial FID4, synchronized FID1–FID3 descriptions, corrected a back-layer text mirror, and moved one conflicting C13 silk segment to fabrication graphics.
4. Made the +3V3 pour explicitly solid-connected to its pads. Its previous zero-clearance, no-pad-connect geometry was not evidence of an open circuit, but obscured the intended connection style.
5. Removed retired bare-chip RF/clock net assignments and added the missing protected probe/debug/battery net classes. This exposed previously unenforced SENSE rules at the local input fanout.
6. Kept the long sensing-channel 0.6 mm separation, 1 mm ground spacing and 3 mm switching separation. A bounded 3.35 × 3.3 mm front-side `FDC_InputFanout` area permits 0.2 mm local SENSE escapes at U3/R30/R31. The two sides of each series input resistor are the same sensing channel and use 0.2 mm separation, rather than being mistaken for separate channels. The existing U3 pad-to-pad package exemption remains last in rule precedence. These are geometric exceptions, not a noise/crosstalk qualification.
7. Moved the 0.4 mm GND diagonal beside the FDC input pads onto B.Cu with two 0.6/0.3 mm vias, preserving its width and endpoints and removing the front-layer sense-to-ground spacing conflict. All-track DRC and refill pass.

No capacitor values, GPIO assignments, module placement, sensing electrode geometry or board outline were changed.

## Verification and limits

- [Final DRC](final-drc.json): **0 errors, 0 unconnected, 0 parity**, with zone refill and all-track error checking enabled. **10 footprint-library mismatch warnings remain** (C13, C21–C27, U2, U4). Customized board copies should be reconciled with approved local library variants before manufacturing; do not blindly replace their geometry.
- [Final ERC](final-erc.json): **0 errors, 10 existing capacitor-symbol library-copy warnings**. These do not imply disconnected nets, but remain library maintenance work.
- [Tests](tests.txt): **43 passed, 261 subtests passed**. Initial failures were stale net-class settings and incomplete expected bare-copper model coverage; recorded in [baseline output](tests-baseline.txt).
- [Schematic preservation](../schematic-review-2026-09-05/verification.json): all **58 nets**, **44 component values/footprints**, and pin numbers/names/types match the baseline.
- [Layer overview](layers-overview.png) and individual [SVGs](layers/) were exported from the final filled board and visually reviewed. The [assembled 3D preview](assembled-preview.png) includes U1 via a review-only copy with its JLC-stage DNP flag removed. The manufacturing source keeps that flag. This is a visual assembly check, not a numerical solid-interference or enclosed RF analysis; the actual cell, screws and enclosure require physical validation.
- [Source hashes](source-sha256.json) identify the final reviewed KiCad sources. Current sweeps are analytical screening only. No hardware, thermal FEA or validated converter transient simulation was run.

## Remaining tasks

1. Qualify C21/C23 and total module-loaded VOUT effective capacitance; revise the reservoir selection if it cannot meet the limits.
2. Implement/verify module firmware pinctrl, regulator mode scheduling, FDC sequencing and heater/radio mutual exclusion as appropriate.
3. Run the bounded battery/load/ripple/I²C bench procedure in the component and power reports, including cold/depleted cells and bus back-power behavior.
4. Reconcile remaining footprint and capacitor-symbol library-copy warnings without overwriting deliberate land changes.
5. Develop a smaller placement jointly with antenna clearance, holder, mounting and sensor-airflow/enclosure constraints; then reroute and repeat DRC/ERC/RF qualification.
