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

**X1 is selected: Micro Crystal CM8V-T1A, 32.768 kHz, C_L 7 pF, ±20 ppm, TA, QC.**
Verified against the nRF54L15 LFXO table (§11.9.2), every parameter:

| nRF54L15 requires | Spec | CM8V-T1A 7 pF | |
|---|---|---|---|
| Load capacitance C_L | 6–9 pF | **7.0 pF** | mid-range, margin both ways |
| Shunt capacitance C0 | typ 1.0, max 2.0 pF | 1.2 pF typ | ok |
| Equivalent series resistance R_S | typ 60, max 100 kΩ | 55 typ / 70 max kΩ | ok |
| Drive level P_D | max 0.5 µW | 0.5 µW max | exactly matched |
| Frequency tolerance (BLE) | ±500 ppm | ±20 ppm | far tighter than needed |
| Package | 2012 2-pin | 2.0 × 1.2 × 0.60 mm | ok |

7 pF is a better choice than the 9 pF the reference BOM suggested — 9 sits at the
hard maximum, 7 sits mid-window with room for PCB stray either side. Ordering
code pattern: `CM8V-T1A 32.768 kHz 7.0 pF ±20 ppm TA QC`.

Footprint is Micro Crystal's own land pattern (`XTAL_CM8V-T1A_2012`, 0.8 × 1.5 mm
pads on 1.5 mm centres). KiCad's generic 2012 footprints do not match it — the
hand-solder variant uses 1.05 mm pads on 1.85 mm centres and the nominal uses
0.6 mm on 1.4 mm.

| | X1 (LFXO) — SELECTED | X2 (HFXO) |
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

Candidate family for X2, **ordering code not confirmed**:
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
| J2 | JST PH `B3B-PH-K` | 8 mm | JST GH `SM03B-GHS-TB` **horizontal** | **4.25 mm** |
| J3 | JST PH `B2B-PH-K` | 8 mm | JST GH `SM02B-GHS-TB` **horizontal** | **4.25 mm** |
| J4 | `PinHeader_2x05_P1.27mm_Vertical_SMD` | ≈6 mm | Tag-Connect `TC2050-IDC-NL` | 0 |

Heights measured from the vendor STEP models KiCad ships, not from a vendor
blurb. JST GH is rated **1 A** (JST GH series page, AWG #26), comfortably over
the 500 mA charge current.

**Vertical and horizontal GH are the same height** — 4.20 mm for `BM**B-GHS-TBT`
against 4.25 mm for the side-entry `SM**B-GHS-TB`, on an identical 4.95 mm board
footprint. The choice between them is cable exit direction, not height: the cell hangs
from the lid to within 6.70 mm of the board, and a top-entry header sends the
lead straight up into it. **Side-entry selected.** See LAYOUT.md §9.

Tag-Connect uses the standard 10-pin Cortex debug pinout, which is what J4 was
already wired to, so no net changes. It needs a **TC2050-IDC-NL cable plus a
retaining clip** — no connector is fitted to the board at all, which is where the
height saving comes from. The `-NL` footprint also carries three unnumbered
alignment pads.

Both GH footprints have two `MP` mounting-post pads with no net. That is normal;
they are mechanical.

### L1 — Murata LQM18PN4R7MFRL

Selected over the TDK MLZ1608M4R7WT000, which met Nordic's numbers but landed
exactly on two of them.

| | Nordic requires | TDK MLZ1608M4R7W | **Murata LQM18PN4R7M** |
|---|---|---|---|
| Inductance | 4.7 µH ±20 % | 4.7 ±20 % | 4.7 ±20 % |
| **DC resistance** | **≤ 650 mΩ** | 0.5 Ω ±30 % → **650 mΩ** worst case | 0.44 Ω ±25 % → **550 mΩ** worst case |
| Current | 120 mA | **I_sat 120 mA** at 50 % L drop | 620 mA rated, 40 °C rise |
| Size | 0603 | 1608 metric | 1.6 × 0.8 × 0.8 mm |
| SRF | — | — | 40 MHz min |

**The two current figures are not the same measurement.** TDK publishes both a
saturation current (120 mA, defined where inductance has dropped 50 %) and a
temperature-rise current (350 mA). Murata publishes **no saturation current at
all** — confirmed against both the reference spec and Murata's own product page,
which lists exactly one current parameter: *Rated Current (Temperature Rise) /
Max. 620 mA*. That page also states **DC Resistance (max.) 0.55 Ω** directly,
confirming the 0.44 Ω ±25 % calculation, and the part as **shielded (ferrite
core)** — worth having next to the RF section.

Murata plots an L-vs-current curve for this part with an **X axis running to
1400 mA** against a 4.7 µH Y axis, which implies useful inductance well past
Nordic's 120 mA. That is inference from the axis range, not a measured value —
pull the exact DC-bias curve from
[SimSurfing](https://ds.murata.com/simsurfing/index.html) before volume.

Two smaller notes: this document is stamped **"Reference Only"** and headed
*reference specification*, so the delivery spec may differ; and DCR is not worth
optimising for power here — at the few mA the nRF54L15 DC/DC draws, the 100 mΩ
difference is microwatts, and HARDWARE.md §7 puts the whole wake cycle at 0.6 %
of the budget. The reason to prefer the Murata is **margin against the spec**,
not efficiency.

### D5 — Panjit RB751V-40

DK `3757-RB751V-40_R1_00001CT-ND`, $0.14.

| | Requirement | RB751V-40 |
|---|---|---|
| Forward drop | ~0.3 V so VBUS lands mid-window (HARDWARE.md §4) | 370 mV @ 1 mA |
| Current | ~200 mA | 300 mA |
| Reverse | ≫ 5.5 V, clear of the 22 V VBUS abs max | **40 V** |
| Leakage | low | 500 nA @ 30 V |
| Package | SOD-323 | SOD-323 |

Runner-up **BAT201M3 RRG** has a genuinely lower drop (290 mV @ 10 mA) and 1 A
rating, but only 20 V reverse — thin against the 22 V VBUS ceiling — and 50 µA
leakage, 100× the Panjit. Take it if the drop matters more than the margin.

**Two near-identical part numbers to avoid.** `RB751V-40WS` (Taiwan Semi) and
`RB751V-40X` (Panjit) both quote the same 370 mV @ 1 mA but are rated **30 mA**,
not 300 mA. And BAS70WS / BAT42WS / BAT43WS all quote **1 V** forward drop, which
defeats the point of a Schottky here.

Forward-voltage figures across a distributor table are quoted at different test
currents (1 mA to 1 A) and are not directly comparable. The ranking above holds
at the low currents indoor solar produces; pull the V_f vs I_f curve if the drop
turns out to matter at the real operating point.

### X2 — Epson FA-128, 32 MHz, C_L 8 pF

Ordering form per the datasheet: **`FA-128 32.000000MHz 8.0 +12.0-12.0`**, and
specify the frequency-vs-temperature characteristic separately.

**2016 was never a requirement.** That came from Nordic's reference BOM. The
datasheet characterises two package sizes (§11.9.1) and mandates neither:

| Nordic's characterisation parts | C_L | C0 | R_S |
|---|---|---|---|
| 2.0 × 1.6 mm (`ISTBY_X32M_X2`) | 8 pF | 0.74 pF | 35 Ω |
| 1.2 × 1.0 mm (`ISTBY_X32M_X3`) | 8 pF | 0.42 pF | 100 Ω |

The 1.2 × 1.0 part passes at **100 Ω** because its C0 is only 0.42 pF. C0 and ESR
trade against each other on the Figure 17 curve; package size is just a proxy.

FA-128 against the requirements:

| nRF54L15 requires | Spec | FA-128 |
|---|---|---|
| Total tolerance | **±40 ppm** | ±12 initial + ±12 temp (−20…+75 °C) + ±1 aging = **25 ppm** |
| | | or ±12 + ±17 (−30…+85 °C) + ±1 = 30 ppm |
| Load capacitance | 6–9 pF | specifiable, 6 pF to ∞ |
| Drive level | ≤ 100 µW | 200 µW max, 10 µW recommended |
| ESR vs C0 | Figure 17 curve | **60 Ω max** at 26–54 MHz |

At C_L = 8 pF the curve allows ~100 Ω for C0 ≈ 0.74 pF, so 60 Ω passes with
margin. **Caveat: the FA-128 datasheet does not publish C0.** Nordic's 2.0 × 1.6
characterisation figures (C0 0.74 pF, R_S 35 Ω) match this part's geometry and
ESR class closely enough that it is very likely the same family, but confirm C0
with Epson before committing.

**Check the land pattern before fab.** Epson's recommended footprint is four
pads on a roughly 1.45 × 1.15 mm envelope; KiCad's generic
`Crystal_SMD_2016-4Pin_2.0x1.6mm` uses 0.9 × 0.8 mm pads on ±0.7 / ±0.55 mm
centres, giving a 2.3 mm outer span. That is a bigger mismatch than the one that
forced a vendor footprint for X1 — expect to build an Epson-specific footprint.

### Cell — Adafruit 1578, 500 mAh

DK `1528-1841-ND`, $7.95. Li-ion pouch, 3.7 V, **29.0 × 36.0 × 4.8 mm**, with PCM.

Chosen over the larger 258 (1200 mAh) for fit margin. The 258 is 34.0 mm across
a 34.92 mm interior — 0.9 mm total — and its datasheet part code is `503562`,
implying a **35 mm nominal** cell that would not fit at all. Pouch cells also
swell. 1578 is 29 mm across, leaving 6 mm of slack, and costs 0.5 years of
runtime (2.9 vs 3.45).

The 1551WK leaves **11.70 mm** between the board top face and the lid. A cell
adhered to the lid at thickness T leaves 11.70 − T of component clearance, and
the tallest part on the board is J2/J3 at 4.25 mm. Box interior is
74.92 × 34.92 mm, so the cell needs its short side ≤ 34.92 and long side ≤ 74.92.

Everything in the Adafruit range that fits, with runtime from
`0.95·C / (0.24·C + 42.8)`:

| P/N | mAh | mm | Clearance left | Runtime |
|---|---|---|---|---|
| 258 | 1200 | 34.0 × 62.0 × 5.0 | 6.70 mm | 3.45 yr — 0.9 mm width margin |
| **1578** | **500** | 29.0 × 36.0 × 4.8 | **6.90 mm** | **2.92 yr — selected** |
| 4236 | 420 | 35.0 × 24.0 × 5.2 | 6.50 mm | 2.78 yr |
| 4237 | 350 | 32.5 × 25.4 × 5.0 | 6.70 mm | 2.62 yr |
| 2750 | 350 | 36.0 × 20.0 × 5.6 | 6.10 mm | 2.62 yr |
| 1317 | 150 | 19.8 × 26.0 × 3.8 | 7.90 mm | 1.81 yr |
| 1570 | 100 | 11.5 × 31.0 × 3.8 | 7.90 mm | 1.42 yr |

Ruled out: **2011** (2000 mAh) and **328** (2500 mAh) are 36 mm and 50 mm across,
over the 34.92 mm interior. **3898** is 8.2 mm thick, which leaves 3.5 mm and
fouls the connectors. The 18650s and the 4.4/6.6/10 Ah packs are far too big.

258 beats the 503450 this design was sized around — same 5.0 mm thickness and
34 mm width, but 1200 mAh instead of 1000, and it is a stocked catalogue part.

**Two things to settle before ordering.**

**J2 is a 2-pin JST PH so the cell plugs straight in** — Adafruit's whole range
ships with a PH plug, and re-crimping a battery lead is a job worth avoiding.
That drops the pack-NTC pin, which costs nothing: Adafruit cells are 2-wire with
no thermistor, so the NTC path was always TH1.

**PH is 8 mm tall against 6.90 mm of clearance under the cell**, so J2 has to sit
outside the cell footprint. The cell covers only 36 mm of the 74 mm board, so the
y 62–74 band keeps its full 11.70 mm — J2 lives there, at y 66.8–72.3.
`tools_gen_pcb.py` asserts this: any part in `COMPONENT_HEIGHTS` taller than the
under-cell gap must not overlap `CELL_RECT`.

### Other open selections

| Ref | Requirement | Candidate |
|---|---|---|
| L1 | 4.7 µH, 120 mA, ±20 %, DCR ≤ 650 mΩ, 0603 | **Murata LQM18PN4R7MFRL** — selected |
| L10 | 2.2 µH, I_sat > 350 mA, I_max > 200 mA, DCR ≤ 400 mΩ | **Murata DFE201610P-2R2M** (footprint already set) |
| D5 | Schottky, low V_f, SOD-323, ~200 mA | **Panjit RB751V-40_R1_00001** — selected |
| J1 | USB-C receptacle, 16P USB2.0 | **HRO TYPE-C-31-M-12** (footprint already set) |
| Solar pre-reg | 5.0 V out, V_IN ≥ 18 V, low I_Q | TPS62122 (buck) or TPS7A1650 (LDO) — **not selected** |
| Cell | ≤ 6.5 mm thick, ≤ 34.92 × 74.92 mm | **Adafruit 1578**, 500 mAh, 29 × 36 × 4.8 mm — selected |
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
| D5 | RB751V-40 Schottky | `D_SOD-323_HandSoldering` |
| FB1 | FB 120R@100MHz | `L_0402_1005Metric_Pad0.77x0.64mm_HandSolder` |
| J1 | USB-C receptacle | `USB_C_Receptacle_HRO_TYPE-C-31-M-12` |
| J2 | Battery - Adafruit 1578 | `JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` |
| J3 | Solar panel | `JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal` |
| J4 | SWD 10p 1.27mm | `Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical` |
| J5 | Antenna feed | `TestPoint_Pad_D1.0mm` |
| L1 | LQM18PN4R7MFRL 4.7uH | `L_0603_1608Metric_Pad1.05x0.95mm_HandSolder` |
| L2 | 2.7nH LQP03HQ2N7B02 | `L_0201_0603Metric` |
| L3 | 3.5nH LQP03HQ3N5B02 | `L_0201_0603Metric` |
| L4 | 3.5nH LQP03HQ3N5B02 | `L_0201_0603Metric` |
| L10 | 2.2uH Isat>350mA DCR<400m | `L_Murata_DFE201610P` |
| NT1 | GND_PA to GND (under U1, F.Cu) | `NetTie_VSSPA` |
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
| X1 | CM8V-T1A 32.768kHz CL=7pF 20ppm | `XTAL_CM8V-T1A_2012` |
| X2 | FA-128 32MHz CL=8pF | `Crystal_SMD_2016-4Pin_2.0x1.6mm` |

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
