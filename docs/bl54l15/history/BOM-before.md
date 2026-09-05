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
CR2032 retainer and installed cell (~5.6 mm). Only the debug contact pattern remains:

| Ref | Part | Height | Note |
|---|---|---|---|
| J4 | Tag-Connect `TC2050-IDC-NL` | 0 | nothing soldered; needs the TC2050 cable + retaining clip |

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

Replaces the retired PMIC buck inductor (same designator, different part). The
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
| C26 | 1uF/10V X7R — +3V3_FDC_SW | `C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` |
| C27 | 100nF X7R — local SHT45 bypass | `C_0201_0603Metric` |
| C28 | 100nF/10V X7R — local FDC1004 bypass | `C_0201_0603Metric` |
| BT1 | CR2032 retainer — MPD BU2032SM-BT-GTR | `BatteryHolder_MPD_BU2032SM-BT-GTR` |
| FB1 | FB 120R@100MHz — MMZ1005S121CT000 | `L_0402_1005Metric_Pad0.77x0.64mm_HandSolder` |
| L1 | MLZ1608M4R7WT000 4.7uH | `L_0603_1608Metric_Pad1.05x0.95mm_HandSolder` |
| L2 | 2.7nH LQP03HQ2N7B02 | `L_0201_0603Metric` |
| L3 | 3.5nH LQP03HQ3N5B02 | `L_0201_0603Metric` |
| L4 | 3.5nH LQP03HQ3N5B02 | `L_0201_0603Metric` |
| L10 | Murata DFE201210U-2R2M=P2 2.2uH | `IND_Murata_DFE201210U` |
| R1 | 1k 1% | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R22 | 4.7k to VOUT | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| R23 | 4.7k to VOUT | `R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` |
| U1 | nRF54L15-QFAA | `QFN48_6X6_NOR` |
| U2 | nPM2100-QEAA | `QFN-16-1EP_4x4mm_P0.65mm_EP2.7x2.7mm_ThermalVias` |
| U3 | FDC1004 | `MSOP-10_3x3mm_P0.5mm` |
| U4 | SHT45-AD1F | `Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad` |
| X1 | CM8V-T1A 32.768kHz CL=7pF 20ppm | `XTAL_CM8V-T1A_2012` |
| X2 | FA-128 32MHz CL=8pF | `XTAL_FA-128_2016_4Pin` |

The nPM2100 QFN, Murata boost-inductor, and MPD holder footprints are now built
and assigned. The two locked mechanical footprints live in
`lib/footprints.pretty` and retain the manufacturer drawing dimensions above.

### JLCPCB assembly audit — 2026-09-03

This is a live-catalog snapshot, not a lifetime procurement guarantee. It was
generated from the schematic BOM using the
[jlcsearch API](https://jlcsearch.tscircuit.com), whose catalog and stock data
are rebuilt from [jlcparts](https://yaqwsx.github.io/jlcparts/). Re-run the
search immediately before ordering because JLC stock and Basic/Preferred status
change.

The assembly BOM now excludes J4 (the bare Tag-Connect land pattern), NT1/NT2,
and TP1/TP2/TP3. They are copper features, not purchasable placements. Both the
schematic and placed PCB mark them out of BOM and position-file exports, and the
board generator reapplies those flags if it is ever revived.

#### Fee-free ordinary passives

These are the preferred assignments for unconstrained passives. Basic and
Preferred parts have no feeder-loading fee in JLC Economic PCBA. The stock
figures below are the live values returned by jlcsearch on 2026-09-03.

| Refs | MPN | LCSC | JLC class | Stock | Why |
|---|---|---:|---|---:|---|
| C4, C7, C8, C10 | CL05B104KO5NNNC | C1525 | Basic | 16,407,331 | 100 nF, 16 V, X7R, ±10%, 0402 |
| C5 | 0402B222K500NT | C1531 | Preferred | 722,028 | 2.2 nF, 50 V, X7R, ±10%, 0402 |
| C12 | CL05B103KB5NNNC | C15195 | Basic | 2,532,413 | 10 nF, 50 V, X7R, ±10%, 0402 |
| C21 | CL05A106MQ5NUNC | C15525 | Basic | 2,281,323 | 10 µF, 6.3 V, X5R, ±20%, 0402 |
| C25 | CL05A225MQ5NSNC | C12530 | Basic | 862,626 | 2.2 µF, 6.3 V, X5R, ±20%, 0402 |
| C26, if X5R is approved | CL05A105KA5NQNC | C52923 | Basic | 4,519,174 | 1 µF, 25 V, X5R, ±10%, 0402; see open decision below |
| R1 | 0402WGF1001TCE | C11702 | Basic | 2,610,919 | 1 kΩ, ±1%, 62.5 mW, 0402 |
| R22, R23 | 0402WGF4701TCE | C25900 | Basic | 3,285,378 | 4.7 kΩ, ±1%, 62.5 mW, 0402 |

Using these seven Basic types plus the one Preferred type avoids up to eight
Economic-PCBA extended-part feeder fees compared with arbitrary extended
equivalents. At JLC's 2026-08-20 rate of $3.07 per extended type, that is up to
**$24.56 per order**.

#### Extended parts that match the design

Do not replace the RF network, crystals, ferrite, or converter inductors merely
to remove feeder fees. Their electrical constraints are worth more than the
one-time setup saving.

| Refs | Selected / proposed MPN | LCSC | Stock | Notes |
|---|---|---:|---:|---|
| C1, C2 | GRM155D80J225KE95D | C907753 | 8,333 | 2.2 µF, 6.3 V, X6T, ±10%, 0402; tighter than the required ±20% |
| C3 | CL10X106MO8NRNC | C3039688 | 127,997 | 10 µF, 16 V, X6S, ±20%, **0603**; matches the placed footprint, not the stale `0402` text in the value |
| C6 | GJM0335C1E1R5WB01D | C435397 | 18,347 | Exact 1.5 pF RF part; the orderable suffix is `D` |
| C9 | GJM0335C1E2R0WB01D | C668326 | 5,874 | Exact 2.0 pF RF part; the orderable suffix is `D` |
| C11 | GRM0335C1ER30BA01D | C88909 | 13,195 | Exact 0.3 pF RF part |
| C13 | 0402CG3R9C500NT | C1566 | 33,467 | 3.9 pF, 50 V, C0G, ±0.25 pF, 0402; manufacturer data confirms tolerance code `C` |
| C22, C24 | 0201B102K500NT | C66942 | 42,968 | 1 nF, 50 V, X7R, ±10%, 0201; X7R exceeds the X5R temperature class |
| C23 | GRM155R60J226ME11D | C415703 | 159,077 | 22 µF, 6.3 V, X5R, ±20%, 0402; **candidate only until its 3.3 V DC-bias curve proves the required effective capacitance** |
| FB1 | MMZ1005S121CT000 | C92036 | 13,241 | Exact ferrite |
| L1 | MLZ1608M4R7WT000 | C76799 | 120,881 | Exact nRF DC/DC inductor |
| L2 | LQP03HQ2N7B02D | C7216765 | 41,904 | Exact 2.7 nH RF part; orderable suffix is `D` |
| L3, L4 | LQP03HQ3N5B02D | C3911055 | 18,376 | Exact 3.5 nH RF part; orderable suffix is `D` |
| L10 | DFE201210U-2R2M=P2 | C2049745 | 14,163 | Exact boost inductor |
| U2 | NPM2100-QEAA-R7 | C46968654 | 1,211 | Exact tape-and-reel order code; catalog package metadata is incomplete, so confirm the JLC footprint preview |
| U3 | FDC1004DGSR | C2865994 | 5,671 | Exact MSOP-10 device |
| U4 | SHT45-AD1F-R2 | C5360602 | 1,492 | Exact PTFE-membrane sensor |
| X1 | CM8V-T1A-32.768KHZ-7PF-20PPM-TA-QC | C5136974 | 38,491 | Exact 7 pF LFXO |
| X2 | Q22FA12800025 | C187794 | 8,310 | Epson FA-128, 32 MHz, 8 pF, ±10 ppm |

With the fee-free assignments above, this design still has **19 extended part
types**, or about **$58.33 in feeder fees per Economic PCBA order** at the
2026-08-20 rate. That dominates a five-board prototype order but amortizes to
about $0.58/board at 100 boards.

At the one-piece prices returned by jlcsearch, the proposals above—including
C52923 for C26 and the still-unverified C415703 for C23—cost about **$13.74 per
board before U1 and BT1**. U4, U3, and U2 account for roughly 54%, 22%, and 12%
of that subtotal, so cheaper resistors and capacitors will not materially change
unit cost.

#### Blocking and optional decisions

- **U1 is not in the public JLC catalog.** Use the full order code
  `nRF54L15-QFAA-R7` and obtain a JLC global-sourcing/consigned-parts quote. Do
  not substitute the package or an older nRF device.
- **BT1 exact MPN `BU2032SM-BT-GTR` is not in the public catalog.** The stocked
  `BU2032SM-JJ-GTR` is not footprint-compatible. Hand-fit BT1 after assembly or
  consign the locked part.
- **C3 has a documentation mismatch:** the schematic value says `0402` but its
  actual footprint is imperial 0603. The C3039688 proposal intentionally follows
  the copper. Correct the value text when the part is locked.
- **C26 has a dielectric mismatch:** the schematic says X7R while this document
  previously said X5R. If X5R is acceptable, Basic part C52923
  (`CL05A105KA5NQNC`, 1 µF, 25 V, ±10%, 0402) removes one feeder fee. If X7R is
  mandatory, use an extended X7R part and add $3.07/order.
- **U4 is the only large unit-cost lever without a PCB or firmware redesign.**
  SHT41-AD1F-R2 (C7461862) keeps the PTFE membrane and SHT4x interface/land
  pattern and was $3.987 with 1,190 in stock, saving about **$3.38 per board**,
  but RH accuracy relaxes from SHT45's ±1.0% typical to ±1.8% typical and
  temperature accuracy from ±0.1 °C to ±0.2 °C. Make that an explicit product
  requirement decision, not an assembly substitution.

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
B.Cu.** See LAYOUT.md §2. There is no third net tie — Nordic's nPM2100
reference circuit grounds PVSS directly with no net tie, and the boost loop
guidance (nwp_058 §4.2) is about placement, not a separate net.

### Integrated antenna and matching provisions

J5 (Hirose U.FL), Molex 2069940100 and its coax are removed from this revision.
AE1 is the board's copper radiator, excluded from BOM and placement exports.

| Ref | Initial fit | Footprint | Procurement |
|---|---|---|---|
| R27 | 0 Ω | `Resistor_SMD:R_0402_1005Metric` | Select an orderable JLC 0402 jumper; final RF value may change after tuning |
| C29 | DNP | `Capacitor_SMD:C_0402_1005Metric` | Do not populate initially; select RF C0G capacitor or inductor from VNA tuning |
| AE1 | PCB copper | `footprints:Monopole_24mm_2450MHz` | No purchased part or paste aperture |

C29 must be excluded with `--exclude-dnp` in assembly exports. R27 remains in
the assembly BOM. The existing L2/L3/L4/C6/C9/C11 radio filter is retained.
See LAYOUT.md §3 for fabrication, keepout and prototype tuning requirements.

### 2026-09-04 layout audit update

C27 is now 0201 on the SHT45 tab. Added C28, 100 nF / 10 V X7R, 0201,
across FDC1004 VDD/GND. Exact orderable parts for these two 0201 bypasses
remain to be selected; the older 0402 C1525 sourcing row does not apply to them.
C26 retains the schematic X7R requirement. See `docs/audit-2026-09-04.md`.
