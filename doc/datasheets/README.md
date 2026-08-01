# Datasheets

The exact document revisions this design was verified against. HARDWARE.md and
BOM.md cite section and table numbers from *these* files — pulling a newer
revision from the vendor may renumber them.

| File | Ref | Part | Revision | Pages |
|---|---|---|---|---|
| [nRF54L15.pdf](nRF54L15.pdf) | U1 | Nordic nRF54L15-QFAA wireless SoC | v1.0 | 940 |
| [nPM1300.pdf](nPM1300.pdf) | U2 | Nordic nPM1300-QEAA PMIC | v1.3 | 175 |
| [FDC1004.pdf](FDC1004.pdf) | U3 | TI FDC1004 capacitance-to-digital converter | Rev. C | 35 |
| [SHT4x.pdf](SHT4x.pdf) | U4 | Sensirion SHT45-AD1F humidity/temp sensor | version 5 | 24 |
| [TPS7A1650.pdf](TPS7A1650.pdf) | U5 | TI TPS7A16 60 V LDO | Rev. F | 37 |

The nRF54L15 document covers nRF54L15/L10/L05 as a family. Only the L15-QFAA
columns apply here.

## Not yet collected

Passives and connectors are sourced from BOM.md rather than from local PDFs.
The two crystals (X1 Micro Crystal CM8V-T1A, X2 Epson FA-128) were spec-checked
against vendor datasheets during selection — see BOM.md § "Crystals" — but those
PDFs are not committed here.
