# BOM and part selection — BL54L15 carrier

**Routing review, 2026-09-04; not an order or fabrication release.**
The full product contains U1 **Ezurio 453-00001R**, DigiKey cut tape
[776-453-00001RCT-ND](https://www.digikey.com/en/products/detail/ezurio/453-00001R/26224851).
This is the 14 × 10 mm BL54L15 with PCB antenna. Do not substitute BL54L15µ or
453-00044 external-antenna versions.

U1 is marked **DNP for the JLC assembly stage**, excluded from position files,
and retained in the complete product BOM. Fit it separately with paste and hot
air after JLC assembly; its underside LGA pads require reflow, not iron access.
The fabrication mask/copper retains all 39 lands. JLC paste excludes U1; a
separate module-only paste layer is exported for local assembly.

The prior parts-selection research is preserved in
[the pre-migration BOM](docs/bl54l15/history/BOM-before.md). Its RF/X2/L1/FB1
selections, counts, costs and stock figures are historical. Current remaining
order codes below are carried from that 2026-09-03 research, not a fresh stock
or price check. No components have been ordered.

## Current product components

This table follows the actual PCB, with procurement metadata in
[parts.json](docs/bl54l15/parts.json). J4 and TP1–TP3 are bare PCB features,
excluded from purchasing and placement exports.

| Ref | Value | Footprint | MPN / LCSC | Status |
|---|---|---|---|---|
| U1 | 453-00001R BL54L15 | `Ezurio_BL54L15_453-00001` | 453-00001R / — | HAND FIT; DNP at JLC; required in finished product |
| BT1 | BU2032SM-BT-GTR | `BatteryHolder_MPD_BU2032SM-BT-GTR` | BU2032SM-BT-GTR / — | Locked footprint; JLC consignment or hand fit unresolved |
| C3 | 10uF/16V X6S | `C_0603_1608Metric` | CL10X106MO8NRNC / C3039688 | 10uF 16V X6S 0603; verify total effective VOUT capacitance |
| C13 | 3.9pF C0G | `C_0402_1005Metric` | 0402CG3R9C500NT / C1566 | 3.9pF C0G standard 0402 |
| C21 | 10uF/6.3V X5R | `C_0402_1005Metric` | CL05A106MQ5NUNC / C15525 | Existing selection |
| C22 | 1nF X5R | `C_0201_0603Metric` | 0201B102K500NT / C66942 | X7R meets temperature requirement |
| C24 | 1nF X5R | `C_0201_0603Metric` | 0201B102K500NT / C66942 | X7R meets temperature requirement |
| C23 | 22uF/6.3V X5R | `C_0402_1005Metric` | GRM155R60J226ME11D / C415703 | CANDIDATE ONLY: effective VINT capacitance at bias unverified |
| C25 | 2.2uF/6.3V X5R | `C_0402_1005Metric` | CL05A225MQ5NSNC / C12530 | Existing selection |
| C26 | 1uF/10V X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | TBD / — | OPEN: select 1uF X7R 0402; X5R C52923 not approved |
| C27 | 100nF X7R | `C_0201_0603Metric` | TBD / — | OPEN: exact 100nF X7R 0201 order code |
| C28 | 100nF/10V X7R | `C_0201_0603Metric` | TBD / — | OPEN: exact 100nF 10V X7R 0201 order code |
| L10 | 2.2uH 20% DFE201210U-2R2M=P2 | `IND_Murata_DFE201210U` | DFE201210U-2R2M=P2 / C2049745 | Locked 2.2uH boost inductor |
| R1 | 1k 1% | `R_0402_1005Metric` | 0402WGF1001TCE / C11702 | 1k 1% standard 0402 |
| R22 | 4.7k to +3V3 | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | 0402WGF4701TCE / C25900 | Existing 4.7k 1% selection |
| R23 | 4.7k to +3V3 | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | 0402WGF4701TCE / C25900 | Existing 4.7k 1% selection |
| U2 | nPM2100-QEAA | `QFN-16-1EP_4x4mm_P0.65mm_EP2.7x2.7mm_ThermalVias` | NPM2100-QEAA-R7 / C46968654 | Confirm JLC footprint preview |
| U3 | FDC1004 | `MSOP-10_3x3mm_P0.5mm` | FDC1004DGSR / C2865994 | Existing MSOP10 selection |
| U4 | SHT45-AD1F | `Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad` | SHT45-AD1F-R2 / C5360602 | PTFE membrane; no substitution |
| X1 | CM8V-T1A 32.768kHz CL=7pF 20ppm | `XTAL_CM8V-T1A_2012` | CM8V-T1A-32.768KHZ-7PF-20PPM-TA-QC / C5136974 | 7pF 20ppm retained external LFXO |

## Retained constraints and open selections

- X1 uses the exact Micro Crystal 2012 two-pad land pattern, CL 7 pF, ±20 ppm,
  ESR 70 kΩ maximum and maximum drive 0.5 µW. Internal load banks are enabled
  in firmware; calculate and trim them as described in
  [the port notes](firmware/BL54L15-port.md). X2 is now inside U1.
- C3 is 10 µF / 16 V X6S **0603**; the stale 0402 value and hand-solder-pad
  mismatch are fixed in both schematic and board. R1/C13 use standard 0402.
- C23 remains a candidate until its bias/temperature data meets nPM2100's VINT
  requirement. C26 remains X7R; the old X5R cost proposal was not accepted.
  C27/C28 need exact order codes matching their existing 0201 lands.
- U1 supply ripple and total effective VOUT capacitance require qualification.
  Existing host capacitors on VOUT total 12.3 µF nominal, before module input
  capacitance. Check the converter's 15 µF upper bound as well as the minimum.
- L10 stays Murata DFE201210U-2R2M=P2: 2.2 µH, 2 A saturation rating and
  228 mΩ DCR, in its verified manufacturer footprint.
- BT1 stays MPD BU2032SM-BT-GTR. The earlier catalog check found no exact JLC
  stock; consignment or separate fitting remains open. BU2032SM-JJ-GTR is not
  footprint-compatible. The CR2032 cell is installed only after hot work.
- Preserve SHT45-AD1F and its PTFE membrane; do not downgrade to SHT41.
- The 11.70 mm enclosure height above the board is unchanged. Module body
  height is nominally 1.6 mm; the existing holder/cell (~5.6 mm) still dominates.
  Keep nylon RF-end screws and the battery removal/programming access.

## Deleted from purchasing and PCB

X2, AE1, L1–L4, FB1, C1/C2/C4–C12, C29, R27 and NT1/NT2 are retired.
Their internal-regulator, HF-clock and RF nets are absent from the current
netlist. The module does **not** replace C3, X1, the reset filter or the PMIC,
sensor and bus support components.

See [assembly and verification](docs/bl54l15/README.md) and
[the export workflow](docs/bl54l15/manufacturing.md).

## Protection additions — 2026-09-04

| Ref | Exact MPN | Function / assembly |
|---|---|---|
| Q1 | DMG2305UX-7 | Reverse-battery PMOS, SOT-23 |
| D1–D3 | TPD1E1B04DPYR | Power ESD clamps, TI DPY0002A; all on F.Cu |
| D4–D10 | TPD1E01B04DPYR | Low-capacitance signal ESD clamps, TI DPY0002A |
| R30–R31 | RC0402FR-075K1L | 5.1 kohm 1%, 0402, sense isolation |
| R32–R35 | RC0402FR-07100RL | 100 ohm 1%, 0402, debug isolation |

All additions are fitted, not DNP. Distributor codes/availability are unverified.
All protection parts use front-side PCBA. D1 fits beside the positive battery
contact in the revised holder courtyard. [Implementation and qualification](docs/protection/README.md).
