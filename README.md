# nRF Moisture Sensor

CR2032-powered BLE soil-moisture and temperature/humidity sensor using Ezurio BL54L15, nPM2100, FDC1004 and SHT40.

Open [nrf-moisture-sensor.kicad_pro](nrf-moisture-sensor.kicad_pro) in KiCad. The maintained schematic and PCB are authoritative; the retired full-design generators must not overwrite them.

- [Latest design review and remaining tasks](docs/design-review-2026-09-05/README.md)
- [Readable schematic PDF](docs/schematic-review-2026-09-05/nrf-moisture-sensor-schematic.pdf)
- [Power copper and current sweeps](docs/power-review-2026-09-05/README.md)
- [I²C pin and capacitor review](docs/component-review-2026-09-05/README.md)
- [Board shrink concept](docs/design-review-2026-09-05/shrink-feasibility.md)
- [Source-derived BOM](BOM.md), [hardware rationale](HARDWARE.md), [firmware](firmware/README.md)

The design is not yet qualified for fabrication: effective capacitance, radio ripple, battery transients and remaining library mismatches need resolution.
