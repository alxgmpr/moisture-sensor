> Subsequent status: Alex updated the PCB and the regenerated JLC export has zero unconnected items and zero schematic parity issues. See [Rev A checkpoint](../rev-a-checkpoint/README.md). This document records the earlier schematic-only step.

# Consolidated schematic implementation

Implemented all agreed BOM optimizations in `nrf-moisture-sensor.kicad_sch`.
PCB file and routing are unchanged by this work; Alex will update the board.

- C21/C23 now match C3: CL10A106MA8NRNC / C96446, 10 µF 25 V X5R.
  **Their assigned footprints change from 0402 to 0603.**
- C26 now matches C25: CL05A225MQ5NSNC / C12530, 2.2 µF 6.3 V X5R, 0402.
- D1/D2/D3 now match D4–D10: TPD1E01B04DPYR / C779389; symbol library IDs
  and datasheet fields also updated. Existing DPY footprint retained.
- R30/R31 now match the four I²C pull-ups: 0402WGF4701TCE / C25900, 4.7 kΩ.
- U4 is SHT40-AD1B-R2 / C2909890, without the integrated membrane. Existing
  four-pad SHT4x footprint without a central solder pad is retained.
- R1 and C13, their isolated wires/labels and C13's GND symbol are removed.
  Former SWD_RST labels now use NRESET, directly joining U1.7, U2.10, R35.2
  and TP15.1. Keep D7 and R35. The PCB update must bridge former R1 rather
  than leave its series path open. Schematic notes updated to match.

## Verification

- Before/after exported KiCad XML netlists compared pin-by-pin: the only net
  changes are deletion of R1/C13 and merging SWD_RST into NRESET. All other
  component-pin connectivity is preserved.
- ERC: **zero errors, nine existing library-symbol mismatch warnings**.
  Baseline had zero errors and eleven warnings. See [ERC](erc.json).
- Grouped native BOM export has **14 assembly purchase lines**, four capacitor
  SKUs, one diode SKU and two resistor SKUs. U1 remains JLC-stage DNP for manual fit.
  [Review BOM](JLC-BOM-review.csv) and [full product BOM](Product-BOM.csv).
- Rendered schematic exported and visually inspected at module/reset, PMIC,
  sensors and protection sections. No new overlapping changed-value text found.
- PCB SHA-256 before and after this work is identical. No PCB parity/DRC claim:
  board update remains outstanding by user instruction.

The existing suite includes checks of the previous exact reservoir selection and
old schematic/PCB parity; these have not been changed to conceal the intentional
handoff mismatch. Use the netlist/ERC evidence above for this schematic-only step.
Finish board synchronization before updating the coupled board expectations and
running fabrication validation.

Capacitor choices implement the requested development plan; effective-capacitance
corner checks, startup/ripple and sensing measurements remain outstanding as
recorded in the [design decision](../dev-bom-consolidation-2026-09-09.md).
The BOM files here are schematic review exports, not a new routed fabrication package.
