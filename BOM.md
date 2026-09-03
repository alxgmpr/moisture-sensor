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

With the retired rechargeable pack removed, the available internal height is
**11.70 mm** above the PCB over the electronics band. The tallest items are the
CR2032 retainer and installed cell (~5.6 mm) and
the U.FL connector (2.4 mm mated). Only two connectors remain:

| Ref | Part | Height | Note |
|---|---|---|---|
| J4 | Tag-Connect `TC2050-IDC-NL` | 0 | nothing soldered; needs the TC2050 cable + retaining clip |
| J5 | Hirose U.FL `U.FL-R-SMT-1(10)` | 2.4 mm | mate-once, see below |

J2 (battery) and J3 (solar) are deleted with the architecture change — the
CR2032 sits in an on-board retainer and there is no external power input at all.

Tag-Connect uses the standard 10-pin Cortex debug pinout, which is what J4 was
already wired to, so no net changes.

### L1 — TDK MLZ1608M4R7WT000

**Changed from the Murata LQM18PN4R7MFRL. Closed — this was an open item and
should not have been.**

The Murata was picked for "margin against the spec": 620 mA rated against
Nordic's 120 mA, and 550 mΩ worst-case DCR against the 650 mΩ limit. But the
620 mA is a **temperature-rise** rating, and Murata publishes **no saturation
current at all** for this part. In a buck, saturation is the parameter that
matters — a thermal rating tells you the part will not cook, not that it will
still be an inductor. The design was carrying an unanswerable question.

**Nordic's "requirement" is this part's datasheet row.** The nRF54L15 reference
BOM (datasheet §14, QFAA circuit configuration 1) lists
`L1  4.7 µH  Inductor, 120 mA, ±20%, 650 mΩ  0603`. The MLZ1608M4R7WT000 row in
TDK's `inductor_commercial_decoupling_mlz1608_en` is:

| | TDK datasheet | Nordic's line |
|---|---|---|
| L | 4.7 µH | 4.7 µH |
| Tolerance | ±20 % | ±20 % |
| DC resistance | 0.5 Ω ±30 % → **650 mΩ** max | 650 mΩ |
| **I_sat** | **120 mA** | 120 mA |
| Size | 1608 metric | 0603 |

All four match. So "the TDK lands exactly on two of Nordic's numbers", which is
why it was rejected the first time, is circular — those numbers were copied from
this part. It is not marginal against the spec; it *is* the spec.

TDK's footnote defines the rating precisely: *"Current assumed when inductance
ratio has decreased by 50 % max."* It also publishes I_temp = 350 mA typ, so both
mechanisms are specified.

**And 120 mA is not a converter requirement.** The nRF54L15's REGULATORS
electrical specification (§11.14) publishes recommended VDD, the power-fail
comparator thresholds and nothing else — no DC/DC peak inductor current, no
switching frequency. (The nPM2100 on this board *does* state a converter-driven
peak requirement — 550 mA on L10, HARDWARE.md §3 — but the nRF54L15 states
none for L1.)

**What the part actually carries.** The buck steps VDD 3.3 V down to the 0.9 V
DECD rail, and DECD feeds DECA/DECRF through FB1, so essentially all active
current passes through L1:

| Condition | I at VDD | Average through L1 |
|---|---|---|
| RX 1M/2M | 2.1 mA | 6.5 mA |
| TX 0 dBm | 3.7 mA | 11.5 mA |
| TX max power, QFN | 9.1 mA | 28.4 mA |
| TX max + 3 mA CPU/peripherals | 12.1 mA | 37.7 mA |

Ripple adds ±17 mA at 4 MHz or ±9 mA at 8 MHz for 4.7 µH, so the **worst-case
peak is around 60 mA** — and that is at maximum TX power, which this design does
not use (indoor, to a BLE proxy that is already deployed; LAYOUT.md §3 calls the
link budget forgiving). At 0 dBm it is under 30 mA peak.

**60 mA against a 120 mA half-inductance point is about 2×**, on the part whose
numbers Nordic quoted. That is the answer, and it needed a current estimate
rather than a trip to SimSurfing.

**What it costs.** TDK's 650 mΩ worst case against Murata's 550 mΩ, at 37.7 mA,
is 0.89 mW against 0.75 mW — 0.14 mW, for 300 ms an hour, or about **0.1 mAh/yr
out of 163**. Below the noise on every other term in HARDWARE.md §7.

### L10 — boost inductor, 2.2 µH, I_sat > 550 mA

Replaces the old nPM1300 buck inductor (same designator, different part). The
nPM2100 permits **2.2 µH ±20% only** — other inductances break the control loop
(nwp_058 §3.1) — and requires **I_sat > 550 mA** because the hysteretic ULP/LP
peak current (typ. 150 mA) plus startup transients are set by the converter, not
the load. DCR < 300 mΩ (PS §9.3.2 BOM).

Candidates with efficiency measured on the nPM2100 EK (nwp_058 Tables 4–5,
VBAT 2.9 V → VOUT 3.3 V):

| Part | Size | Efficiency @ 100 µA / 120 mA | I_sat | DCR |
|---|---|---|---|---|
| **Murata DFE201210U-2R2M=P2** | 2012 | 91.9% / 94.7% | 2000 mA | 228 mΩ |
| TDK MLP2016H2R2MT0S1 | 2016 | 91.5% / 95.0% | 550 mA | 110 mΩ |
| Samsung CIGT201610EH2R2MNE | 2016 | 90.6% / 95.1% | 2900 mA | 73 mΩ |

**Select the Murata** — it is the efficiency/margin midpoint, it is the same
2012 size family as the old part, and its 2 A I_sat clears the 550 mA floor by
3.6×. This selection is locked as **Murata `DFE201210U-2R2M=P2`**. Footprint
`footprints:IND_Murata_DFE201210U` uses the manufacturer-pattern 2.00 × 1.20 mm
body, two 0.55 × 1.20 mm pads on 1.45 mm centres (0.90 mm inner gap), and a
2.70 × 1.90 mm courtyard.

### X2 — Epson FA-128, 32 MHz, C_L 8 pF

Ordering form per the datasheet: **`FA-128 32.000000MHz 8.0 +10.0-10.0`**, and
specify the frequency-vs-temperature characteristic and operating temperature
range separately.

**Corrected from `+12.0-12.0`.** Field ④ of Epson's ordering code is
*frequency tolerance at +25 °C*, and the datasheet's standard value for that is
**±10 × 10⁻⁶**, not ±12. The ±12 figure is the *frequency-versus-temperature*
characteristic over −20…+75 °C, which is field ⑤ and a separate specification.
The old code asked for a non-standard +25 °C tolerance and would have invited a
"contact us" quote for no benefit. Using the standard ±10 also improves the
budget below rather than costing anything.

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
| Total tolerance | **±40 ppm** | **±10** initial + ±12 temp (−20…+75 °C) + ±1 aging = **23 ppm** |
| | | or ±10 + ±17 (−30…+85 °C) + ±1 = 28 ppm |
| Load capacitance | 6–9 pF | specifiable, 6 pF to ∞ |
| Drive level | ≤ 100 µW | 200 µW max, 10 µW recommended |
| ESR vs C0 | Figure 17 curve | **60 Ω max** at 26–54 MHz |

At C_L = 8 pF the curve allows ~100 Ω for C0 ≈ 0.74 pF, so 60 Ω passes with
margin.

**C0 is confirmed absent from the datasheet — this one stays open.** Re-read
`FA-128_en.pdf` end to end. The Specifications table gives f_nom, T_stg, T_use,
DL, f_tol, f_tem, C_L, R1 and f_age, and there is **no C0 row anywhere**, so this
is not an oversight in the earlier reading. Nordic's 2.0 × 1.6 characterisation
figures (C0 0.74 pF, R_S 35 Ω) match this part's geometry and ESR class closely
enough that it is very likely the same family, but it remains the one FA-128
parameter that has to come from Epson directly. It is half of what the Figure 17
ESR curve checks, so it is worth an email before committing to volume.

Also confirmed from the datasheet while checking: **ESR R1 = 60 Ω max** for
26 MHz ≤ f_nom ≤ 54 MHz, **drive level 200 µW max with 10 µW recommended**, and
**pads #2 and #4 are connected to the cover and must go to ground.**

**Land pattern — corrected 2026-08-01, placement rework still open.**
`footprints:XTAL_FA-128_2016_4Pin` now carries Epson's recommended land:
**0.95 × 0.85 mm pads on 1.45 mm (X) × 1.15 mm (Y) centres**, a 2.40 × 2.00 mm
outer envelope, X being the crystal's 2.0 mm axis.

The earlier version of this footprint had **0.50 × 0.85 mm pads on 0.95 × 1.15
centres** and a 1.45 × 2.00 envelope. That came from misreading the four callouts
on Epson's footprint drawing. They are not interchangeable — read them by where
the dimension arrows terminate:

| Callout | Terminates on | Role |
|---|---|---|
| 1.45 | pad centres | pitch, X |
| 0.95 | pad edges | pad width, X |
| 1.15 | pad centres | pitch, Y |
| 0.85 | pad edges | pad height, Y |

Taking 1.45 as the outer envelope and 0.95 as the X pitch produced a land 0.95 mm
short in X. Against the part's own terminals (centres ±0.625 on the 2.0 mm axis,
±0.475 on the 1.6 mm axis, from the bottom-view 0.65/0.6 and 0.5/0.45 callouts)
the old land gave a 0.05 mm toe on the long axis and **zero margin on either side
of the short axis** — pad and terminal exactly coincident. Epson's land gives a
0.20 mm toe beyond the package edge on both axes.

`Crystal_SMD_2016-4Pin_2.0x1.6mm` was rejected on the same misreading. It is
0.9 × 0.8 mm pads on 1.4 × 1.1 centres, a 2.30 × 1.90 envelope — within 0.05 mm
of Epson on every dimension and with the same corner numbering, so it is a
perfectly good substitute. The custom footprint is kept only because it holds
Epson's exact figures, the way `XTAL_CM8V-T1A_2012` does for X1.

Pad numbering was already right and is unchanged: **#1 and #3 are the crystal
terminals, #2 and #4 are the cover and go to ground**, with #1 bottom-left in
Epson's top view. X2's placement angle moved from −90° to 180° so that the same
pad still faces the same way on the board; XC1 and XC2 still land on pads 1 and 3.

**Open:** the corrected land does not fit the routing that was laid around the
undersized pads. DRC gains 14 errors, all local to X2 — pad 3 shorts a +3V3
track, pad 4 shorts the XC1 track, and pads 1 and 3 now reach the `ZoneB_GND_F`
pour. The +3V3 and XC1/XC2 approach need re-routing and X2 may need to move; see
LAYOUT.md before re-filling zones.

The 3D model (`lib/FA-128 32.0000MF10Z-AJ0.STEP`) is attached to both the
`.kicad_mod` and the placed instance, rotated `(90 0 90)` to follow the land's
long axis moving from Y to X. Its orientation still has not been checked in the
3D viewer, and the file's internal `FILE_NAME` is `FA-128 54.0000MF15Z-E3.STEP`
— a 54 MHz variant, same body, but not the part we are buying.

### Cell — CR2032, and the holder

Any major-brand **CR2032** (Panasonic, Murata, Duracell) — 225 mAh nominal,
LiMnO₂, 20 mm × 3.2 mm, ~10-year shelf life, ~1%/yr self-discharge. The fuel
gauge's default LiMnO₂ model is the CR2032 (nan_048 §3), so no battery-model
work is needed. User-replaceable; battery-out is the off switch; the board ships
without a cell.

**Holder — locked:** MPD **`BU2032SM-BT-GTR`**, top-entry SMT CR2032 retainer.
Footprint `footprints:BatteryHolder_MPD_BU2032SM-BT-GTR` follows MPD's drawing:
two 3.20 × 4.20 mm pads on 29.30 mm centres, 32.50 mm total copper span, and a
31.86 × 22.40 mm installed-cell/assembly envelope. The courtyard adds a marked
10.50 × 4.00 mm removal-tool access extension. The board silk carries explicit
`+` and `−` markings because the accepted architecture has no reverse-protection
FET. BT1 is placed crosswise at board-local (17.0, 42.0), with pad 1/positive
toward U2.

### Other open selections

| Ref | Requirement | Candidate |
|---|---|---|
| L1 | 4.7 µH, ±20 %, DCR ≤ 650 mΩ, published I_sat, 0603 | **TDK MLZ1608M4R7WT000** — selected |
| L10 | 2.2 µH ±20%, I_sat > 550 mA, DCR < 300 mΩ | **Murata DFE201210U-2R2M=P2** — selected, see above |
| U2 | primary-cell PMIC, boost to 3.3 V, load switch, fuel gauge | **nPM2100-QEAA** (QFN16) — selected |
| BT1 | CR2032 SMD retainer, 20 mm, Zone B | **MPD BU2032SM-BT-GTR** — locked |
| Cell | CR2032, any major brand | LiMnO₂ 225 mAh, ~10-yr shelf life |
| Enclosure | **Hammond 1551WKBK**, PC, 80 × 40 × 22 mm | + 4× nylon #2 screws for the antenna-end holes; now IP54, see NEXT-STEPS.md §5 |

**Deleted with the architecture change:** J1 (USB-C), J2 (battery JST), J3 (solar
JST), D5 (solar Schottky), U5 (TPS7A1650), C30/C31 (solar caps), D3/D4 + R25/R26
(charge LEDs), TH1 (pack NTC), R20/R21 (VSET straps — the nPM2100's VSET is
NC and SYSGDEN grounds directly). Their selection notes are preserved in git
history at commit 1753c18 and belong to board 2 now.

The coin-cell retainer and boost inductor are no longer open selections.

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
| C21 | 10uF/6.3V X5R — VBAT | `C_0402_1005Metric` |
| C22 | 1nF X5R — VBAT RF | `C_0201_0603Metric` |
| C23 | 22uF/6.3V X5R — VINT | `C_0402_1005Metric` |
| C24 | 1nF X5R — VINT RF | `C_0201_0603Metric` |
| C25 | 2.2uF/6.3V X5R — VOUT | `C_0402_1005Metric` |
| C26 | 1uF/10V X5R — FDC_VDD | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C27 | 100nF X7R | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| BT1 | CR2032 retainer — MPD BU2032SM-BT-GTR | `BatteryHolder_MPD_BU2032SM-BT-GTR` |
| FB1 | FB 120R@100MHz — MMZ1005S121CT000 | `L_0402_1005Metric_Pad0.77x0.64mm_HandSolder` |
| J4 | SWD 10p 1.27mm | `Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical` |
| J5 | U.FL antenna | `U.FL_Hirose_U.FL-R-SMT-1_Vertical` |
| L1 | MLZ1608M4R7WT000 4.7uH | `L_0603_1608Metric_Pad1.05x0.95mm_HandSolder` |
| L2 | 2.7nH LQP03HQ2N7B02 | `L_0201_0603Metric` |
| L3 | 3.5nH LQP03HQ3N5B02 | `L_0201_0603Metric` |
| L4 | 3.5nH LQP03HQ3N5B02 | `L_0201_0603Metric` |
| L10 | Murata DFE201210U-2R2M=P2 2.2uH | `IND_Murata_DFE201210U` |
| NT1 | GND_PA to GND (under U1, F.Cu) | `NetTie_VSSPA` |
| NT2 | GND_C9 to GND (B.Cu only) | `NetTie-2_SMD_Pad0.5mm` |
| R1 | 1k 1% | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R22 | 4.7k to VOUT | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R23 | 4.7k to VOUT | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| TP1 | SENSE1 | `TestPoint_Pad_D1.0mm` |
| TP2 | SENSE2 | `TestPoint_Pad_D1.0mm` |
| TP3 | SHLD | `TestPoint_Pad_D1.0mm` |
| TP4 | SHPHLD | `TestPoint_Pad_D1.0mm` |
| U1 | nRF54L15-QFAA | `QFN48_6X6_NOR` |
| U2 | nPM2100-QEAA | `QFN-16-1EP_4x4mm_P0.65mm_EP2.7x2.7mm_ThermalVias` |
| U3 | FDC1004 | `MSOP-10_3x3mm_P0.5mm` |
| U4 | SHT45-AD1F | `Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad` |
| X1 | CM8V-T1A 32.768kHz CL=7pF 20ppm | `XTAL_CM8V-T1A_2012` |
| X2 | FA-128 32MHz CL=8pF | `XTAL_FA-128_2016_4Pin` |

The nPM2100 QFN, Murata boost-inductor, and MPD holder footprints are now built
and assigned. The two locked mechanical footprints live in
`lib/footprints.pretty` and retain the manufacturer drawing dimensions above.

---

## Notes on specific parts

**U4 SHT45-AD1F** — no copper under the sensor except the four pin pads, and the
die pad must not be soldered. The `_NoCentralPad` footprint handles the pad; the
copper keepout is yours to draw. See LAYOUT.md §8.

**TP4 keeps the SHPHLD net testable.** SHPHLD is otherwise unconnected
(HARDWARE.md §3); the test point gives the bench a place to ground it for
ship-mode entry tests without holding a probe on a QFN pad.

**J4** — Tag-Connect TC2050-IDC-NL, standard 10-pin Cortex pinout: pin 1 VTref,
2 SWDIO, 3 GND, 4 SWDCLK, 5 GND, 6 SWO, 7/8 NC, 9 GND, 10 nRESET. Nothing is
soldered to the board; you need the cable and a retaining clip.

**NT1 / NT2** — net ties, not real parts (`in_bom no`). They exist so the DRC can
enforce Nordic's two RF grounding rules, which are otherwise invisible in a
netlist. **NT1 must be placed under the U1 centre pad on F.Cu; NT2 must be on
B.Cu.** See LAYOUT.md §2. The nPM1300's NT3 is deleted — Nordic's nPM2100
reference circuit grounds PVSS directly with no net tie, and the boost loop
guidance (nwp_058 §4.2) is about placement, not a separate net.

**J5 removed-then-restored history.** There is no test point on the antenna feed.
A 1.0 mm pad on a 2.4 GHz feed is roughly 0.1–0.2 pF of shunt capacitance — the
same order as C11 at 0.3 pF — so it perturbs the impedance it exists to measure.
Tuning a PCB IFA is done by soldering a coax pigtail directly to the feed trace,
shield to the adjacent ground pour, and removing it afterwards; that needs no
footprint.

### J5 — Hirose U.FL-R-SMT-1(10), antenna connector

Replaces the PCB inverted-F. See LAYOUT.md §3 for why. Verified against the
Hirose U.FL catalogue drawing: **50 Ω, DC–8 GHz**, V.S.W.R. ≤1.3 to 3 GHz,
mated height 1.9–2.4 mm nominal (2.5 mm max), **30 mating cycles**, 15.7 mg,
7.7 mm² mounting area. Footprint `Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical`.

Mated height is nothing against the 6.70 mm of clearance under the cell, and J5
sits in the y 0–11.5 band that the cell does not cover anyway.

**Production antenna: Molex `2069940100`.** It is a 15.4 × 6.4 mm adhesive
2.4 GHz flex antenna with 100 mm of 1.13 mm coax and a U.FL-compatible plug.
Mount it vertically on the inside RF-end short wall, perpendicular to the PCB.
Maintain at least 25 mm radiator-to-cell spacing, use nylon screws at the RF-end
holes, and restrain the coax around the enclosure perimeter without sharp bends
or routing it across the cell or switching loop. U.FL is rated for 30 mating
cycles, so treat it as mate-once.
