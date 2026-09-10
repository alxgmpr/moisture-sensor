> Rev A checkpoint: consolidated schematic and updated PCB match the JLC export. See [checkpoint and Rev B follow-ups](docs/rev-a-checkpoint/README.md).

# nRF Moisture Sensor — Bill of Materials

Generated from the maintained schematic on 2026-09-09 using KiCad's BOM exporter.
The [source CSV](docs/schematic-consolidation-2026-09-09/Product-BOM.csv) includes manufacturer and assembly-stage DNP fields.
This supersedes the earlier manually maintained selection table; historical selections remain in Git.

U1 is required in the finished product but marked DNP for the JLC assembly stage and fitted separately.
The CR2032 cell is not included as a schematic component. Bare PCB features are excluded from purchasing.
No stock, price, or fabrication approval is implied by this export.

| Ref | Value | Footprint | MPN | Manufacturer | LCSC | JLC DNP |
| --- | --- | --- | --- | --- | --- | --- |
| BT1 | CR2032-BS-6 | footprints:BatteryHolder_LianXin_CR2032-BS-6 | CR2032-BS-6 | Lian Xin Technology | C22363833 |  |
| C3 | 10uF/25V X5R | Capacitor_SMD:C_0603_1608Metric | CL10A106MA8NRNC | Samsung | C96446 |  |
| C21 | 10uF/25V X5R | Capacitor_SMD:C_0603_1608Metric | CL10A106MA8NRNC | Samsung | C96446 |  |
| C22 | 1nF 50V X7R | Capacitor_SMD:C_0402_1005Metric | 0402B102K500NT | FH | C1523 |  |
| C23 | 10uF/25V X5R | Capacitor_SMD:C_0603_1608Metric | CL10A106MA8NRNC | Samsung | C96446 |  |
| C24 | 1nF 50V X7R | Capacitor_SMD:C_0402_1005Metric | 0402B102K500NT | FH | C1523 |  |
| C25 | 2.2uF/6.3V X5R | Capacitor_SMD:C_0402_1005Metric | CL05A225MQ5NSNC | Samsung | C12530 |  |
| C26 | 2.2uF/6.3V X5R | Capacitor_SMD:C_0402_1005Metric | CL05A225MQ5NSNC | Samsung | C12530 |  |
| C27 | 100nF 16V X7R | Capacitor_SMD:C_0402_1005Metric | CL05B104KO5NNNC | Samsung | C1525 |  |
| C28 | 100nF 16V X7R | Capacitor_SMD:C_0402_1005Metric | CL05B104KO5NNNC | Samsung | C1525 |  |
| D1 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| D2 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| D3 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| D4 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| D5 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| D6 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| D7 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| D8 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| D9 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| D10 | TPD1E01B04DPYR | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E01B04DPYR | Texas Instruments | C779389 |  |
| L10 | 2.2uH 20% DFE201210U-2R2M=P2 | footprints:IND_Murata_DFE201210U | DFE201210U-2R2M=P2 | Murata | C2049745 |  |
| Q1 | DMG2305UX-13 | Package_TO_SOT_SMD:SOT-23 | DMG2305UX-13 | Diodes Incorporated | C144153 |  |
| R22 | 4.7k 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF4701TCE | UNI-ROYAL | C25900 |  |
| R23 | 4.7k 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF4701TCE | UNI-ROYAL | C25900 |  |
| R30 | 4.7k 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF4701TCE | UNI-ROYAL | C25900 |  |
| R31 | 4.7k 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF4701TCE | UNI-ROYAL | C25900 |  |
| R32 | 100 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF1000TCE | UNI-ROYAL | C25076 |  |
| R33 | 100 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF1000TCE | UNI-ROYAL | C25076 |  |
| R34 | 100 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF1000TCE | UNI-ROYAL | C25076 |  |
| R35 | 100 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF1000TCE | UNI-ROYAL | C25076 |  |
| R36 | 4.7k 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF4701TCE | UNI-ROYAL | C25900 |  |
| R37 | 4.7k 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF4701TCE | UNI-ROYAL | C25900 |  |
| U1 | 453-00001R BL54L15 | footprints:Ezurio_BL54L15_453-00001 | 453-00001R | Ezurio |  | DNP |
| U2 | nPM2100-QEAA | Package_DFN_QFN:QFN-16-1EP_4x4mm_P0.65mm_EP2.7x2.7mm_ThermalVias | NPM2100-QEAA-R7 | Nordic Semiconductor | C46968654 |  |
| U3 | FDC1004 | Package_SO:MSOP-10_3x3mm_P0.5mm | FDC1004DGSR | Texas Instruments | C2865994 |  |
| U4 | SHT40-AD1B | Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad | SHT40-AD1B-R2 | Sensirion | C2909890 |  |
| X1 | CM8V-T1A 32.768kHz CL=7pF 20ppm | footprints:XTAL_CM8V-T1A_2012 | CM8V-T1A-32.768KHZ-7PF-20PPM-TA-QC | Micro Crystal | C5136974 |  |

All resistors and capacitors use standard KiCad reflow footprints. D1–D10 use
`Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm`. The module, crystal, inductor,
and battery holder retain their verified part-specific footprints.

## Qualification items

- C21/C23 now use CL10A106MA8NRNC, 10 µF 0603. Verify ≥3.5 µF effective over actual VBAT/VINT bias, temperature, tolerance and aging; these are development selections, not newly qualified capacitors.
- Qualification and current firmware: [reliability work](docs/reliability-2026-09-07/README.md).
- VOUT: C3 + C25 + C27 total 12.3 µF nominal, before module loading. Check both 0.7 µF minimum and 15 µF maximum effective limits. LDOSW draws from VINT; C26/C28 do not directly add to VOUT.
- C26/C27/C28 are now selected in the schematic as listed above; earlier TBD and 0201 descriptions were stale.
- Preserve the exact BL54L15 antenna module, SHT40-AD1B opening (no integrated membrane), inductor footprint, and X1 load/drive requirements. Keep the cell out during hot work.
- Qualify module supply ripple and low-battery radio/heater transients before release.

See the [component review](docs/component-review-2026-09-05/README.md) and [power review](docs/power-review-2026-09-05/README.md) for evidence and test procedures.

Current schematic revision implements the consolidated development BOM. PCB update and layout are assigned to Alex. See [implementation record](docs/schematic-consolidation-2026-09-09/README.md); older cost-review selections are historical.
