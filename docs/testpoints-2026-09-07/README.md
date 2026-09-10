# Added test points — 7 September 2026

Added 14 front-side, 1 mm test pads (TP4–TP17) to the maintained PCB and schematic. TP1–TP3 remain SENSE1, SENSE2 and SHLD. All test pads are excluded from BOM and placement exports and have no paste opening.

[Assembled-board test-point map](assembled-head.png) · [front copper](front-head.png) · [inner routing](inner-head.png) · [schematic](schematic.svg)

Coordinates below are absolute KiCad board millimetres. The short names are printed on front silkscreen; reference designators and full net names remain on the fabrication layer.

| Reference | Board label | Net | X, Y (mm) |
|---|---|---|---|
| TP4 | 3V3 | `+3V3` | 73.775, 58.000 |
| TP5 | GND | `GND` | 71.575, 58.000 |
| TP6 | FDC | `+3V3_FDC_SW` | 74.500, 103.800 |
| TP7 | GND | `GND` | 76.700, 103.800 |
| TP8 | VBAT | `VBAT` | 62.200, 96.500 |
| TP9 | RAW | `/VBAT_RAW` | 62.800, 88.000 |
| TP10 | VINT | `/VINT` | 73.500, 95.000 |
| TP11 | GND | `GND` | 75.700, 95.000 |
| TP12 | SDA | `/SDA` | 79.500, 98.000 |
| TP13 | SCL | `/SCL` | 77.000, 98.000 |
| TP14 | INT | `/PMIC_INT` | 82.000, 98.000 |
| TP15 | RST | `/NRESET` | 85.800, 45.500 |
| TP16 | M1 | `/MARK1` | 68.450, 57.000 |
| TP17 | M2 | `/MARK2` | 66.000, 57.000 |

## Timing markers

- **TP16 / M1 / MARK1 = U1 pad 20, nRF P1.07** (`gpio1`, pin 7 in Zephyr).
- **TP17 / M2 / MARK2 = U1 pad 21, nRF P1.06** (`gpio1`, pin 6 in Zephyr).

These two previously unused GPIOs are reserved for firmware timing markers. Updated 2026-09-09: moved from pads 29/30 to bottom-edge pads 20/21 for outward escape without routing through the ground planes. Pads 29/30 and P0.01/P0.02 are unconnected. Both markers are left unrouted for manual routing. No firmware toggling is enabled by this hardware change. Configure these pins as outputs only when instrumenting firmware; retain the normal low-power state otherwise. Connect the logic-analyzer ground to TP5. The markers use the MCU supply voltage, which follows the main rail.

## Placement and routing

TP4/TP5 sit below C3 for local module-supply probing. TP6/TP7 sit beside the FDC bypass capacitors. TP8 samples protected VBAT after Q1; TP9 samples the raw battery near D1. TP10/TP11 are immediately right of the PMIC capacitor cluster. TP13/TP12/TP14 form the left-to-right SCL/SDA/INT row beside U2. TP15 observes NRESET on the MCU side of the reset filter.

Short local front routes serve VBAT, raw battery and module VDD. Diagnostic branches on In2 avoid disturbing the existing front power loops and bottom signal routes. Seven nearby ground stitching vias were repositioned to clear these branches; no existing functional track, component position, antenna rule area or sensing-zone outline was changed. The ground plane remains connected after refill. TP10 is a voltage-probing point only; VINT is not an external-load supply. Use a short probe ground spring for ripple measurements; the VINT/FDC branches do not replace probing directly across the bypass capacitor when investigating very high-frequency noise.

The 3D review includes the hand-fitted radio module and shows all new pads outside component bodies. The existing battery-holder STEP is a substitute, so final enclosure and actual-holder probe access still need physical confirmation.

## Verification

- Native KiCad DRC: zero errors, zero unconnected items, zero schematic parity issues; ten pre-existing library-footprint mismatch warnings.
- Native KiCad ERC: zero errors; ten pre-existing library-symbol warnings.
- Exported schematic netlist verifies every new test-point net and the two marker-to-module pin mappings.
- Historical validation of the initial 2026-09-07 implementation (superseded by the 2026-09-09 pin swap): comparing every original PCB pad net showed only U1.29/U1.30 changed, from unconnected to MARK1/MARK2. See [connectivity record](connectivity.json).
- Relevant repository checks: 10 tests and 21 subtests pass (module pinout/keepouts, assembly flags, ESD ground returns, PMIC topology, fiducials and fabrication archive). The VINT topology expectation now includes TP10 while still excluding any external load.
- Reviewed the schematic, copper layers and assembled top view.
- Refreshed `production/jlc-economic-quote`: 36 fitted components, 20 BOM groups, matching placement file and 13-file Gerber archive. No new purchased components.

[DRC report](drc.json) · [ERC report](erc.json)
