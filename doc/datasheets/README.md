# Datasheets

The PDFs in this directory are **not tracked** — `.gitignore` holds
`/doc/datasheets/*.pdf`. They are large, they are not ours, and they are all
re-fetchable. This index is the tracked part, and it is the part that matters:
HARDWARE.md and BOM.md cite section, table and figure numbers from *these*
revisions, and vendors renumber between revisions.

To rebuild the directory on a fresh checkout, see [Refetching](#refetching).

## Semiconductors

| File | Ref | Part | Manufacturer | Revision | Pages |
|---|---|---|---|---|---|
| `nRF54L15.pdf` | U1 | nRF54L15-QFAA wireless SoC | Nordic | v1.0 | 940 |
| `nPM2100_Datasheet_v1.0.pdf` | U2 | nPM2100-QEAA primary-cell PMIC | Nordic | v1.0 | 114 |
| `FDC1004.pdf` | U3 | FDC1004 capacitance-to-digital converter | TI | Rev. C | 35 |
| `SHT4x.pdf` | U4 | SHT45-AD1F humidity/temperature sensor | Sensirion | version 5 | 24 |

The nRF54L15 document covers nRF54L15/L10/L05 as a family; only the L15-QFAA
columns apply.

### nPM2100 application documents

| File | Document | Nordic ref | Revision |
|---|---|---|---|
| `nPM2100_HW_Design_Guidelines_nwp_058.pdf` | Hardware Design Guidelines — inductor/capacitor selection, CR2032 reservoir test | nwp_058 | 2025-03-28 |
| `nan_048.pdf` | Using the nPM2100 Fuel Gauge — host library, CR2032 model, state persistence | nan_048 | 2025-07-01 |
| `nPM2100_EK_User_Guide.pdf` | nPM2100 EK (PCA10170) user guide — EK wiring, jumpers | 4532_011 | v0.9.0, 2025-03-28 |
| `nPM2100_Reverse_Battery_ngl_002.pdf` | Reverse battery protection for the nPM2100 | ngl_002 | 2026-03-18 |

HARDWARE.md cites the nPM2100 PS as "PS" and these by their Nordic ref
(nwp_058, nan_048, ngl_002, EK UG).

## Frequency control

| File | Ref | Part | Manufacturer | Pages |
|---|---|---|---|---|
| `CM8V-T1A.pdf` | X1 | CM8V-T1A 32.768 kHz, C_L 7 pF, ±20 ppm | Micro Crystal | 2 |
| `FA-128.pdf` | X2 | FA-128 32 MHz, C_L 8 pF | Epson | 2 |

## Passives

| File | Ref | Part | Manufacturer | Pages |
|---|---|---|---|---|
| `MLZ1608.pdf` | L1 | MLZ1608M4R7WT000 4.7 µH — series sheet | TDK | 6 |
| `LQP03HQ.pdf` | L2, L3, L4 | LQP03HQ series — covers 2N7B02 and 3N5B02 | Murata | 16 |
| `GJM0335C1E1R5WB01.pdf` | C6 | GJM0335 1.5 pF C0G 0201 | Murata | 29 |
| `GJM0335C1E2R0WB01.pdf` | C9 | GJM0335 2.0 pF C0G 0201 | Murata | 29 |

L3 and L4 are the same part, and both LQP03HQ values live in one series sheet.
The two GJM0335 files are per-value exports of the same series document.

## Connectors and mechanical

| File | Ref | Part | Manufacturer | Pages |
|---|---|---|---|---|
| `U.FL-R-SMT-1.pdf` | J5 | U.FL-R-SMT-1(10) — drawing EDC3-302540-10 | Hirose | 1 |
| `TC2050-IDC-NL.pdf` | J4 | TC2050-IDC-NL Plug-of-Nails, no legs | Tag-Connect | 3 |
| `1551WK.pdf` | — | 1551WK enclosure (1551WKBK = black PC) | Hammond | 1 |

`U.FL-R-SMT-1.pdf` and `1551WK.pdf` are vector drawings with no text layer, so
they will not turn up in a full-text search of this directory.

## Superseded — kept as board-2 reference

These parts are off this board's BOM after the coin-cell architecture change,
but the files stay: board 2 (the pump controller) inherits the charging
architecture, and HARDWARE.md §4/§9 point here.

| File | Was | Note |
|---|---|---|
| `nPM1300.pdf` | U2 | board 2's PMIC; the old §3/§9 analysis cites it |
| `TPS7A1650.pdf` | U5 | solar pre-regulator, board 2 |
| `RB751V-40.pdf` | D5 | solar-path Schottky, board 2 |
| `DW01-P.pdf` | — | protection IC inside the old Adafruit 1578 pack |
| `JST_PH.pdf` | J2 | old battery connector |
| `JST_GH.pdf` | J3 | old solar connector |
| `DFE201610P-2R2M.pdf` | L10 | old nPM1300 buck inductor; L10 is now DFE201210U-2R2M |

## Gaps

No datasheet on file, because the BOM does not name a manufacturer part number:

| Ref | Value |
|---|---|
| L10 | Murata DFE201210U-2R2M=P2, 2.2 µH (nwp_058 Table 1) |
| BT1 | CR2032 retainer — MPD BU2032SM-BT-GTR, open until placement |
| C13 | 3.9 pF C0G 0402 |
| — | bulk R and C values (see BOM.md component list) |

C13 is the nRF54L15 RESET filter rather than part of the RF match, but it still
needs a real part number before a production BOM is released.

## Refetching

Everything except the five files below came from the DigiKey Product
Information API v4, via the `digikey` skill's `sync_datasheets_digikey.py`
in `--mpn-list` mode. Given a file of MPNs it re-downloads the lot.

Fetched by hand, and not reproducible that way:

- `nRF54L15.pdf`, `nPM1300.pdf` — Nordic infocenter
- `nPM2100_Datasheet_v1.0.pdf`, `nan_048.pdf` — Nordic's docs site is behind a
  Cloudflare challenge for scripts; both were downloaded in a browser. The three
  other nPM2100 documents (`nwp_058`, EK UG, `ngl_002`) are also served from
  `www.nordicsemi.com/-/media/Software-and-other-downloads/Product-Briefs/` and
  were fetched via the Internet Archive.
- `CM8V-T1A.pdf`, `FA-128.pdf`, `MLZ1608.pdf`, `DW01-P.pdf` — vendor sites
- `1551WK.pdf` — `https://www.hammfg.com/files/parts/pdf/1551WKBK.pdf`
  (DigiKey's link for this one 404s)
