# nRF Moisture Sensor — Bill of Materials

Generated from the maintained schematic on 2026-09-05 using KiCad's BOM exporter.
The [source CSV](docs/design-review-2026-09-05/product-bom.csv) includes manufacturer and assembly-stage DNP fields.
This supersedes the earlier manually maintained selection table; historical selections remain in Git.

U1 is required in the finished product but marked DNP for the JLC assembly stage and fitted separately.
The CR2032 cell is not included as a schematic component. Bare PCB features are excluded from purchasing.
No stock, price, or fabrication approval is implied by this export.

| Ref | Value | Footprint | MPN | LCSC | JLC DNP |
|---|---|---|---|---|---|
| BT1 | CR2032-BS-6 | footprints:BatteryHolder_LianXin_CR2032-BS-6 | CR2032-BS-6 | C22363833 |  |
| C3 | 10uF/16V X6S | Capacitor_SMD:C_0603_1608Metric | CL10X106MO8NRNC | C3039688 |  |
| C13 | 3.9pF C0G | Capacitor_SMD:C_0402_1005Metric | 0402CG3R9C500NT | C1566 |  |
| C21 | 10uF/6.3V X5R | Capacitor_SMD:C_0402_1005Metric | CL05A106MQ5NUNC | C15525 |  |
| C22 | 1nF 50V X7R | Capacitor_SMD:C_0402_1005Metric | 0402B102K500NT | C1523 |  |
| C23 | 22uF/6.3V X5R | Capacitor_SMD:C_0402_1005Metric | GRM155R60J226ME11D | C415703 |  |
| C24 | 1nF 50V X7R | Capacitor_SMD:C_0402_1005Metric | 0402B102K500NT | C1523 |  |
| C25 | 2.2uF/6.3V X5R | Capacitor_SMD:C_0402_1005Metric | CL05A225MQ5NSNC | C12530 |  |
| C26 | 1uF 10V X7R | Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder | GRM155Z71A105KE01D | C528974 |  |
| C27 | 100nF 16V X7R | Capacitor_SMD:C_0402_1005Metric | CL05B104KO5NNNC | C1525 |  |
| C28 | 100nF 16V X7R | Capacitor_SMD:C_0402_1005Metric | CL05B104KO5NNNC | C1525 |  |
| D1 | TPD1E1B04DPYR | footprints:TI_DPY0002A | TPD1E1B04DPYR | C779408 |  |
| D2 | TPD1E1B04DPYR | footprints:TI_DPY0002A | TPD1E1B04DPYR | C779408 |  |
| D3 | TPD1E1B04DPYR | footprints:TI_DPY0002A | TPD1E1B04DPYR | C779408 |  |
| D4 | TPD1E01B04DPYR | footprints:TI_DPY0002A | TPD1E01B04DPYR | C779389 |  |
| D5 | TPD1E01B04DPYR | footprints:TI_DPY0002A | TPD1E01B04DPYR | C779389 |  |
| D6 | TPD1E01B04DPYR | footprints:TI_DPY0002A | TPD1E01B04DPYR | C779389 |  |
| D7 | TPD1E01B04DPYR | footprints:TI_DPY0002A | TPD1E01B04DPYR | C779389 |  |
| D8 | TPD1E01B04DPYR | footprints:TI_DPY0002A | TPD1E01B04DPYR | C779389 |  |
| D9 | TPD1E01B04DPYR | footprints:TI_DPY0002A | TPD1E01B04DPYR | C779389 |  |
| D10 | TPD1E01B04DPYR | footprints:TI_DPY0002A | TPD1E01B04DPYR | C779389 |  |
| L10 | 2.2uH 20% DFE201210U-2R2M=P2 | footprints:IND_Murata_DFE201210U | DFE201210U-2R2M=P2 | C2049745 |  |
| Q1 | DMG2305UX-7 | Package_TO_SOT_SMD:SOT-23 | DMG2305UX-7 | C150470 |  |
| R1 | 1k 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF1001TCE | C11702 |  |
| R22 | 4.7k to +3V3 | Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder | 0402WGF4701TCE | C25900 |  |
| R23 | 4.7k to +3V3 | Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder | 0402WGF4701TCE | C25900 |  |
| R30 | 5.1k 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF5101TCE | C25905 |  |
| R31 | 5.1k 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF5101TCE | C25905 |  |
| R32 | 100 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF1000TCE | C25076 |  |
| R33 | 100 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF1000TCE | C25076 |  |
| R34 | 100 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF1000TCE | C25076 |  |
| R35 | 100 1% | Resistor_SMD:R_0402_1005Metric | 0402WGF1000TCE | C25076 |  |
| U1 | 453-00001R BL54L15 | footprints:Ezurio_BL54L15_453-00001 | 453-00001R |  | DNP |
| U2 | nPM2100-QEAA | Package_DFN_QFN:QFN-16-1EP_4x4mm_P0.65mm_EP2.7x2.7mm_ThermalVias | NPM2100-QEAA-R7 | C46968654 |  |
| U3 | FDC1004 | Package_SO:MSOP-10_3x3mm_P0.5mm | FDC1004DGSR | C2865994 |  |
| U4 | SHT45-AD1F | Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad | SHT45-AD1F-R2 | C5360602 |  |
| X1 | CM8V-T1A 32.768kHz CL=7pF 20ppm | footprints:XTAL_CM8V-T1A_2012 | CM8V-T1A-32.768KHZ-7PF-20PPM-TA-QC | C5136974 |  |

## Qualification items

- C21: demonstrate at least 3.5 µF effective capacitance at fresh-cell voltage, tolerance, temperature and aging; present evidence does not establish sufficient margin.
- C23: qualify the exact 22 µF part's effective VINT capacitance; nominal value alone is insufficient.
- VOUT: C3 + C25 + C27 total 12.3 µF nominal, before module loading. Check both 0.7 µF minimum and 15 µF maximum effective limits. LDOSW draws from VINT; C26/C28 do not directly add to VOUT.
- C26/C27/C28 are now selected in the schematic as listed above; earlier TBD and 0201 descriptions were stale.
- Preserve the exact BL54L15 antenna module, SHT45 membrane, inductor footprint, and X1 load/drive requirements. Keep the cell out during hot work.
- Qualify module supply ripple and low-battery radio/heater transients before release.

See the [component review](docs/component-review-2026-09-05/README.md) and [power review](docs/power-review-2026-09-05/README.md) for evidence and test procedures.
