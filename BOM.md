# BOM & Part Selection

Generated from the netlist. Regenerate the component table after any schematic
change. Companion to [HARDWARE.md](HARDWARE.md) and [LAYOUT.md](LAYOUT.md).

**Footprint policy:** hand-solder variants everywhere they exist. The one
exception is the RF matching network — **L2, L3, L4, C6, C9, C11 stay 0201
standard pads**. Nordic's component values are matched to their reference land
pattern, and hand-solder pads add enough parasitic capacitance at 2.4 GHz to
shift a 0.3 pF capacitor. Don't "fix" those to hand-solder.

MCU support passives are 0402 rather than Nordic's 0201, for assembly. That
needs slightly more room around the QFN48 than the reference layout uses — get
them as close to their pins as the larger pads allow.

---

## Parts still to select

### Crystals — the datasheet constrains these harder than expected

| | X1 (LFXO) | X2 (HFXO) |
|---|---|---|
| Frequency | 32.768 kHz | 32 MHz |
| **Load capacitance C_L** | **6–9 pF — 9 pF max** | **6–9 pF, use 8 pF** |
| Shunt capacitance C0 | 1.0–2.0 pF | see Figure 17 |
| **Max drive level** | **0.5 µW** | 100 µW |
| Frequency tolerance | ±20 ppm (Nordic ref) | **±40 ppm total for BLE** |
| Package | 2012, 2-pin | 2016, 4-pad |

**The C_L ≤ 9 pF limit rules out most 32.768 kHz crystals**, which are commonly
12.5 pF. Filter on load capacitance first, everything else second.

ESR is not a single number — the datasheet gives it as a curve of maximum
allowable ESR against C0 for a given C_L (Figure 17, §5.5.1.2). Check the
candidate's ESR and C0 against that curve rather than looking for a spec line.

Candidate families, **ordering codes not confirmed**:
- X1: Epson FC-12M series (2.0×1.2 mm), C_L 9 pF, ±20 ppm
- X2: Abracon ABM8W-32.0000MHZ-8-B1U-T3, or NDK NX2016SA-32M

No discrete load caps — both oscillators use internal trim banks. See
HARDWARE.md §2.

---

## Connector heights — resolved

The Hammond 1551WK leaves **6.70 mm** of clear component height under the cell
(LAYOUT.md §9). JST PH is 8 mm mounting height per JST's own PH datasheet, and
the 2×5 1.27 mm SWD header is comparable, so all three were changed:

| Ref | Was | Height | Now | Height |
|---|---|---|---|---|
| J2 | JST PH `B3B-PH-K` | 8 mm | JST GH `BM03B-GHS-TBT` | ≈4.7 mm |
| J3 | JST PH `B2B-PH-K` | 8 mm | JST GH `BM02B-GHS-TBT` | ≈4.7 mm |
| J4 | `PinHeader_2x05_P1.27mm_Vertical_SMD` | ≈6 mm | Tag-Connect `TC2050-IDC-NL` | 0 |

JST GH is rated 1 A, comfortably over the 500 mA charge current. Molex PicoBlade
(≈4.0 mm, also 1 A) is the alternative if GH's 1.25 mm crimps prove fiddly.

Tag-Connect uses the standard 10-pin Cortex debug pinout, which is what J4 was
already wired to, so no net changes. It needs a **TC2050-IDC-NL cable plus a
retaining clip** — no connector is fitted to the board at all, which is where the
height saving comes from. The `-NL` footprint also carries three unnumbered
alignment pads.

Both GH footprints have two `MP` mounting-post pads with no net. That is normal;
they are mechanical.

### Other open selections

| Ref | Requirement | Candidate |
|---|---|---|
| L1 | 4.7 µH, 120 mA, ±20 %, DCR ≤ 650 mΩ, 0603 | Murata LQM18 series |
| L10 | 2.2 µH, I_sat > 350 mA, I_max > 200 mA, DCR ≤ 400 mΩ | **Murata DFE201610P-2R2M** (footprint already set) |
| D5 | Schottky, low V_f, SOD-323, ~200 mA | Nexperia PMEG2010AEH |
| J1 | USB-C receptacle, 16P USB2.0 | **HRO TYPE-C-31-M-12** (footprint already set) |
| Solar pre-reg | 5.0 V out, V_IN ≥ 18 V, low I_Q | TPS62122 (buck) or TPS7A1650 (LDO) — **not selected** |
| Cell | **503450**, ~1000 mAh, 5 × 34 × 50 mm, protected | not selected — see HARDWARE.md §7 |
| Enclosure | **Hammond 1551WKBK**, IP68 PC, 80 × 40 × 22 mm | + 4× nylon #2 screws for the antenna-end holes |

**The solar pre-regulator is not on the board yet.** Reserve roughly **8 × 8 mm**
near J3 for the regulator plus its input/output caps and, if you pick the buck,
an inductor. Its output lands on `SOLAR_5V`, which already exists as a net with
TP5 and D5's anode on it.

---

## Component list

| Ref | Value | Footprint |
|---|---|---|
| C1 | 2.2uF/2.5V X6T | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C2 | 2.2uF/2.5V X6T | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C3 | 10uF/6.3V X6S 0402 | `C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` |
| C4 | 100nF X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C5 | 2.2nF X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C6 | 1.5pF GJM0335C1E1R5WB01 | `C_0201_0603Metric` |
| C7 | 100nF X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C8 | 100nF X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C9 | 2.0pF GJM0335C1E2R0WB01 | `C_0201_0603Metric` |
| C10 | 100nF X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C11 | 0.3pF C0G | `C_0201_0603Metric` |
| C12 | 10nF/6.3V X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C13 | 3.9pF C0G | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C20 | 1uF/10V X5R | `C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` |
| C21 | 10uF/25V X5R | `C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` |
| C22 | 10uF/25V X5R | `C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` |
| C23 | 2.2uF/16V X7R | `C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` |
| C24 | 10uF/25V X5R | `C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` |
| C25 | 100nF X5R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C26 | 1uF/10V X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C27 | 100nF X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| D3 | GREEN | `LED_0603_1608Metric_Pad1.05x0.95mm_HandSolder` |
| D4 | RED | `LED_0603_1608Metric_Pad1.05x0.95mm_HandSolder` |
| D5 | OR-ing Schottky | `D_SOD-323_HandSoldering` |
| FB1 | FB 120R@100MHz | `L_0402_1005Metric_Pad0.77x0.64mm_HandSolder` |
| J1 | USB-C receptacle | `USB_C_Receptacle_HRO_TYPE-C-31-M-12` |
| J2 | Battery 503450 + NTC | `JST_GH_BM03B-GHS-TBT_1x03-1MP_P1.25mm_Vertical` |
| J3 | Solar panel | `JST_GH_BM02B-GHS-TBT_1x02-1MP_P1.25mm_Vertical` |
| J4 | SWD 10p 1.27mm | `Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical` |
| J5 | Antenna feed | `TestPoint_Pad_D1.0mm` |
| L1 | 4.7uH 120mA 0603 | `L_0603_1608Metric_Pad1.05x0.95mm_HandSolder` |
| L2 | 2.7nH LQP03HQ2N7B02 | `L_0201_0603Metric` |
| L3 | 3.5nH LQP03HQ3N5B02 | `L_0201_0603Metric` |
| L4 | 3.5nH LQP03HQ3N5B02 | `L_0201_0603Metric` |
| L10 | 2.2uH Isat>350mA DCR<400m | `L_Murata_DFE201610P` |
| NT1 | GND_PA to GND (under U1, F.Cu) | `NetTie-2_SMD_Pad0.5mm` |
| NT2 | GND_C9 to GND (B.Cu only) | `NetTie-2_SMD_Pad0.5mm` |
| R1 | 1k 1% | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R20 | 470k 1% VSET2=3.3V | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R21 | 0R disables BUCK1 | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R22 | 4.7k to +3V3 | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R23 | 4.7k to +3V3 | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R25 | 1k | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R26 | 1k | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| TH1 | 10k B3435 - couple to cell | `R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` |
| TP1 | SENSE1 | `TestPoint_Pad_D1.0mm` |
| TP2 | SENSE2 | `TestPoint_Pad_D1.0mm` |
| TP3 | SHLD | `TestPoint_Pad_D1.0mm` |
| TP4 | SHPHLD | `TestPoint_Pad_D1.0mm` |
| TP5 | SOLAR_5V | `TestPoint_Pad_D1.0mm` |
| U1 | nRF54L15-QFAA | `QFN48_6X6_NOR` |
| U2 | nPM1300-QEAA | `QFN32_5X5_NOR` |
| U3 | FDC1004 | `MSOP-10_3x3mm_P0.5mm` |
| U4 | SHT45-AD1F | `Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad` |
| X1 | 32.768kHz CL=9pF 20ppm | `Crystal_SMD_2012-2Pin_2.0x1.2mm_HandSoldering` |
| X2 | 32MHz CL=8pF 40ppm | `Crystal_SMD_2016-4Pin_2.0x1.6mm` |

---

## Notes on specific parts

**TH1** — the pack has no thermistor (DW01P + 8205A only), so this is fitted,
not DNP, and must be **thermally coupled to the cell**. A board-mounted NTC
measures board temperature and partly defeats the JEITA logic. Consider a
leaded NTC taped to the cell body instead of the 0603 land.

**U4 SHT45-AD1F** — no copper under the sensor except the four pin pads, and the
die pad must not be soldered. The `_NoCentralPad` footprint handles the pad; the
copper keepout is yours to draw. See LAYOUT.md §8.

**D3/D4** — fed from VSYS through R25/R26 and sunk by the nPM1300's LED drivers,
so they only draw when firmware turns them on.

**J4** — Tag-Connect TC2050-IDC-NL, standard 10-pin Cortex pinout: pin 1 VTref,
2 SWDIO, 3 GND, 4 SWDCLK, 5 GND, 6 SWO, 7/8 NC, 9 GND, 10 nRESET. Nothing is
soldered to the board; you need the cable and a retaining clip.

**NT1 / NT2** — net ties, not real parts (`in_bom no`). They exist so the DRC can
enforce Nordic's two RF grounding rules, which are otherwise invisible in a
netlist. **NT1 must be placed under the U1 centre pad on F.Cu; NT2 must be on
B.Cu.** See LAYOUT.md §2.
