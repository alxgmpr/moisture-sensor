# Schematic readability review — 2026-09-05

The editable project is `nrf-moisture-sensor.kicad_sch`, titled **nRF Moisture Sensor**. A printable review is `nrf-moisture-sensor-schematic.pdf`; `after/overview.png` and four cropped images show the final layout.

## Changes

- Repacked the previous mostly empty A1 sheet onto A2. Removed an empty legacy section.
- Added consistent colored functional frames for the radio, module support, SWD, crystal/battery, power, protection, and sensors.
- Made hidden rail names visible, hid internal power reference designators, moved overlapping SHT45 and inductor values, and removed duplicate test-point value text.
- Included C28 inside the sensing group, explicitly distinguished the main 3.3 V and switched FDC supplies, and labeled reset support, I2C pull-ups, the primary-cell restriction, and module assembly intent.
- Corrected the nPM2100 symbol's graphical pin direction/body arrangement and widened pin spacing. Pin names now appear inside the body; connection locations and attached objects moved together. Updated `lib/nordic/NPM2100-QEAA.kicad_sym` to match the embedded symbol.
- Kept the existing DNP attribute on U1; its red cross denotes hand fitting after JLC assembly, as noted on the sheet.

## Verification

`verify_netlist.py` compares before/after exported XML netlists. All **58 nets, 44 component values/footprints, and library pin numbers/names/types are identical**. It writes `verification.json` and fails on any difference.

Final ERC: **0 errors, 10 warnings**. All ten are existing `Device:C_Small` library-copy mismatches; the intentional custom capacitor graphics differ from the installed stock symbol. There is no PMIC library-copy mismatch after synchronizing its project library. No electrical connections, component values, footprints, or PCB placement were changed by this readability pass.

Visual inspection included the original overview, four final regional crops, and repeated revisions of the PMIC, support, and sensor sections. The before/after XML and SVG exports are retained for review.

This pass verifies graphical cleanup and preservation of the existing circuit. Datasheet adequacy, rail current capacity, and physical prototype testing are separate reviews.
