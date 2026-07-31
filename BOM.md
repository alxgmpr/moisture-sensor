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
currents (1 mA to 1 A) and are not directly comparable. The 370 mV figure is
quoted at 1 mA; the solar path now runs up to the 100 mA VBUS current limit
(HARDWARE.md §4), where the drop will be higher. Pull the V_f vs I_f curve
before assuming VBUS lands at 4.63 V under a charging load — 300 mA is the
part's rating, so headroom exists, but the number will move.

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

**Land pattern — done.** `footprints:XTAL_FA-128_2016_4Pin` is built and placed,
and it matches Epson's recommended footprint exactly: **0.50 × 0.85 mm pads on
0.95 mm (X) × 1.15 mm (Y) centres**, a 1.45 × 2.00 mm outer envelope. The
datasheet's own footprint drawing gives 1.45, 0.95, 1.15 and 0.85, which is the
same pattern. KiCad's generic `Crystal_SMD_2016-4Pin_2.0x1.6mm` uses 0.9 × 0.8 mm
pads on ±0.7 / ±0.55 mm centres for a 2.30 mm outer span in X — 0.85 mm wider
than Epson specify, a bigger mismatch than the one that forced a vendor footprint
for X1. The 3D model (`lib/FA-128 32.0000MF10Z-AJ0.STEP`) is attached to both the
`.kicad_mod` and the placed instance; its orientation has not been checked in the
3D viewer yet.

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
| U5 | 5.0 V out, V_IN ≥ 13.9 V, tolerant of a wrong adapter | **TI TPS7A1650DGNR** — selected, see below |
| Panel | V_OC 6–12 V, external, window-mounted | **Voltaic Systems P126** (Adafruit 5366) — selected |
| Cell | ≤ 6.5 mm thick, ≤ 34.92 × 74.92 mm | **Adafruit 1578**, 500 mAh, 29 × 36 × 4.8 mm — selected |
| Enclosure | **Hammond 1551WKBK**, IP68 PC, 80 × 40 × 22 mm | + 4× nylon #2 screws for the antenna-end holes |

**Nothing on this board is open now, and everything is placed.** U5, C30 and C31
sit in the reserve below J3. No inductor is needed — the LDO wins (below) — so
the block is just an HVSSOP-8 and two 0603s, 7.3 × 6.0 mm inside the ~8 × 8 mm
that was set aside.

### The solar path is fitted on every board

The panel is external and lives in a window. Most boards ship without it, so
**J3, D5, U5, C30 and C31 are all populated.** `SOLAR_DNP` at the top of the
solar block in `tools_gen_sch.py` is the single switch; set it to `False` and
re-run for a solar-equipped build. The footprints stay on the board either way,
so a unit can be retrofitted without a respin.

TP5 stays populated — it is a bare pad with nothing to buy.

**The barrel jack is not on the board.** A CUI PJ-102AH is 11.0 mm tall with a
10.7 × 4.7 mm footprint, against the 6.90 mm of clearance under the cell at J3's
position (LAYOUT.md §9). Putting it on the board would have forced the whole
solar block into the y 62–74 end band next to J2. It goes on the panel pigtail
instead, J3 stays the 4.25 mm JST GH it already is, and **no PCB placement or
routing changes at all**.

### Panel — Voltaic Systems P126 (Adafruit 5366)

6 V, 2 W ETFE monocrystalline, external, window-mounted. All figures from the
P126 datasheet (April 2023) at STC, 1000 W/m² 25 °C.

| Symbol | Parameter | Nominal | Expected¹ |
|---|---|---|---|
| V_OC | Open-circuit voltage | **8.59 V** | 8.34 V |
| V_P | Voltage at MPP | **7.09 V** | 6.84 V |
| I_P | Current at MPP | 0.34 A | 0.29 A |
| I_SC | Short-circuit current | 0.37 A | 0.33 A |
| W_P | Max power | 2.38 W | 2.31 W |
| η | Cell efficiency | 21.5 % (SunPower Maxeon) | — |

¹ Voltaic's "expected" column already accounts for cell cutting, encapsulation
losses and the worst cell in the series. Design to it.

| | Requirement | P126 |
|---|---|---|
| V_OC | 6–12 V | 8.59 V, mid-band |
| Loaded voltage | > 5.0 V + LDO dropout across the useful light range | 7.09 V at STC, ~5.9 V at ~5 klx |
| Worst-case V_OC | ≪ 22 V VBUS abs max | 9.23 V at 0 °C |
| Power | ≫ 69 µW average load (HARDWARE.md §7) | 2.38 W STC, ~119 mW on a dull day |
| Environment | sunlit windowsill | IPX7, −40…+85 °C, 10+ yr UV tested |
| Cells in series | — | 12 (8.59 / 12 = 0.716 V/cell) |

Mechanical: **136 × 112 × 3.1 mm**, 79 g, ±0.5 mm, G110 VHB gasket mounting.

**Larger than the enclosure in both axes** — the 1551WK is 80 × 40 mm. The panel
VHB-mounts to a window and reaches the sensor on its own lead. See HARDWARE.md
§4 for why that is the right arrangement rather than a compromise.

**Its plug is 3.5 × 1.1 mm, not 5.5 × 2.1 mm.** Build the pigtail with a
3.5 × 1.1 mm jack, or buy Voltaic's 3.5 → 5.5/2.1 adapter lead if you want the
larger barrel. Do not fit a 5.5 mm jack and expect the panel to mate.

**Why not the Panasonic Amorton pair this document previously specified.** That
choice was correct for the problem as originally posed — hold 5 V at 200 lx of
*room* light, where amorphous silicon's 0.63 V/cell beats crystalline's ~0.4 V.
Once the panel moved to a window at 5,000–50,000 lx the constraint disappeared
and c-Si wins on every axis: roughly 2× the power per unit area, a fraction of
the cost, a laminate built to sit in sunlight, and a low enough V_OC that the
input-rating rule stops being the deciding factor.

### U5 — TI TPS7A1650DGNR

Fixed 5.0 V, HVSSOP-8 (DGN) with PowerPAD. All figures from SBVS171F.

| | Requirement | TPS7A1650 | Source |
|---|---|---|---|
| Output | 5.0 V fixed | 5.0 V, ±2 % | §1 features |
| V_IN operating | ≥ 13.9 V (1.5 × panel V_OC cold) | **3–60 V** | §6.3 |
| V_IN absolute max | > 9.23 V | 62 V | §6.1 |
| Dropout | ≪ the 2.1 V headroom at STC | 60 mV at 20 mA | §6.5, V_DO |
| Ground current | secondary | 5 µA typ, 15 µA max at I_OUT = 10 µA | §6.5, I_GND |
| Output current | ≥ the 100 mA VBUS limit | 100 mA; I_LIM 225 mA typ / 101 mA min | §1, §7.3.5 |
| Thermal | survive a wrong adapter | R_θJA 66.2 °C/W, T_SD 125 °C | §6.4, §6.5 |
| Enable | tie on, no logic available | EN → IN; V_EN_HI 1.2 V min, I_EN ±1 µA | §7 Pin Functions, §6.5 |
| Package | fits the 8 × 8 mm reserve | 3 × 3 mm HVSSOP-8 | DGN0008C |
| Status | orderable | Active / Production, −40…125 °C | Package option addendum |

**Chosen over the TPS62122 buck on input rating, deliberately, after the buck
qualified.** With the P126 the buck clears the 1.5× rule (1.5 × 9.23 = 13.9 V
against 15 V recommended operating), so this is not a disqualification the way it
was with the 16-cell amorphous panel. It loses on judgement:

- The user-facing barrel jack is an unqualified DC input. A 19 V laptop brick
  destroys a 17 V part; the TPS7A1650 rides it out at T_J ≈ 118 °C, inside its
  125 °C shutdown, still regulating.
- The 1.3× harvest advantage buys nothing — the panel already delivers
  1,700–35,000× the board's average load, and the path is capped at 100 mA.
- It would add an inductor, two feedback resistors and a C_ff, plus a project
  footprint: KiCad's `WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm` is 0.375 × 0.4 mm pads
  on ±0.8875 mm against TI's DRV0006 0.45 × 0.3 mm and 1.95 mm span. Same class
  of mismatch as the 2016 crystal.
- A second switching node next to a capacitive front end that LAYOUT.md §6
  already fences off from SW2.

**U5 is a 100 mA part, and that sets a firmware rule.** The nPM1300's VBUS
current limit defaults to IBUS100MA and reverts there on every reset — which is
exactly right for this path. **Do not raise it when running from solar.** See
HARDWARE.md §4; this is the opposite of the USB path's requirement.

Pin handling, from the SBVS171F Pin Functions table:

| Pin | Name | Wired to | Why |
|---|---|---|---|
| 1 | OUT | `SOLAR_5V` | — |
| 2 | FB/DNC | **nothing** | Fixed versions: *"Do not connect to this pin. Do not route this pin to any electrical net, not even GND or IN."* |
| 3 | PG | open | Open-collector, unused. A pull-up would need a rail and burn current |
| 4 | GND | GND | — |
| 5 | EN | `SOLAR_PANEL` | *"If not used, the EN pin can be connected to IN. Make sure that V_EN ≤ V_IN at all times"* — tying them satisfies that identically |
| 6 | NC | open | Datasheet: open or any voltage between GND and IN |
| 7 | DELAY | open | PG delay unused |
| 8 | IN | `SOLAR_PANEL` | — |
| 9 | PowerPAD | GND | *"TI highly recommends connecting the PowerPAD to the GND plane"* |

**Footprint checked, and this one does not need a project part.** TI DGN0008C
specifies 8 pads 1.4 × 0.45 mm on 0.65 mm pitch, rows on 4.4 mm centres, thermal
pad metal ≈ 1.6 × 1.92 mm. KiCad's
`Package_SO:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm` is 1.45 × 0.5 mm on
±2.15 mm with a 1.57 × 1.89 mm pad — generous on every dimension rather than
short, unlike the 2016 land pattern that forced a vendor footprint for X2.

### C30, C31 — LDO input and output capacitors

| | Datasheet requirement (SBVS171F §8.2.1.2.1.3) | Fitted |
|---|---|---|
| C30, input | ≥ 0.1 µF for stability, 10 µF recommended | **4.7 µF / 50 V X5R 0603**, ~1.5 µF at 12 V bias |
| C31, output | ≥ 2.2 µF for stability, 10 µF recommended | **10 µF / 25 V X5R 0603**, ~5 µF at 5 V bias |

**C30 is 50 V because of the barrel jack, not the panel.** The P126 tops out at
9.23 V, which a 25 V part covers easily — but a user-accessible DC jack is an
unqualified input, and U5 is good to 60 V. Rating C30 at 50 V moves the ceiling
off the capacitor and onto U5's thermal limit, which lands at about 19 V at the
100 mA VBUS current limit. It costs one BOM line; C31 stays the same 10 µF/25 V
X5R already at C21/C22/C24.

Check the manufacturer's DC-bias curve rather than the nameplate, as with
C21/C22/C24 — a 50 V 0603 derates hard, and the derated values above are what
have to clear the two minimums. They do, by 15× and 2× respectively.

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
| C30 | 4.7uF/50V X5R | `C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` |
| C31 | 10uF/25V X5R | `C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` |
| D3 | GREEN | `LED_0603_1608Metric_Pad1.05x0.95mm_HandSolder` |
| D4 | RED | `LED_0603_1608Metric_Pad1.05x0.95mm_HandSolder` |
| D5 | RB751V-40 Schottky | `D_SOD-323_HandSoldering` |
| FB1 | FB 120R@100MHz | `L_0402_1005Metric_Pad0.77x0.64mm_HandSolder` |
| J1 | USB-C receptacle | `USB_C_Receptacle_HRO_TYPE-C-31-M-12` |
| J2 | Battery - Adafruit 1578 | `JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` |
| J3 | Solar panel | `JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal` |
| J4 | SWD 10p 1.27mm | `Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical` |
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
| U5 | TPS7A1650 5V LDO | `HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm` |
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

**U5 / C30 / C31** — placed in the reserve below J3: U5 at board
(24.37–30.63, 50.75–54.25), C31 and C30 in a row above it at y 48.27–49.73.
0.57 mm clear of J3 at the tightest and 2.85 mm off the board edge. J3 and D5
did not move. Not yet routed. `SOLAR_5V` now has a real driver (U5 pin 1 is a power output), so
the PWR_FLAG that used to hold that net up in ERC has been removed — two power
outputs on one net is an ERC conflict.

**Solar panel and pigtail** — off-board, not in the component table, and only
needed for a solar-equipped build:

| Item | Part | Note |
|---|---|---|
| Panel | Voltaic Systems **P126** / Adafruit **5366** | 6 V 2 W ETFE, VHB-mounts to a window |
| Barrel jack | 3.5 × 1.1 mm inline socket | **Matches the P126's own plug.** A 5.5 × 2.1 mm jack will not mate |
| — or — | Voltaic 3.5 → 5.5/2.1 adapter lead | If you want the larger common barrel instead |
| Housing | JST **SHR-02V-S-B** | Mates J3 |
| Contacts | JST **SSH-003T-P0.2** ×2 | 26 AWG |

Polarity is set once, when the pigtail is crimped, and centre-positive is the
convention. J3 has no keying against a reversed panel and U5's IN pin is −0.3 V
absolute maximum, so mark the housing at build time.

**J4** — Tag-Connect TC2050-IDC-NL, standard 10-pin Cortex pinout: pin 1 VTref,
2 SWDIO, 3 GND, 4 SWDCLK, 5 GND, 6 SWO, 7/8 NC, 9 GND, 10 nRESET. Nothing is
soldered to the board; you need the cable and a retaining clip.

**NT1 / NT2** — net ties, not real parts (`in_bom no`). They exist so the DRC can
enforce Nordic's two RF grounding rules, which are otherwise invisible in a
netlist. **NT1 must be placed under the U1 centre pad on F.Cu; NT2 must be on
B.Cu.** See LAYOUT.md §2.

**J5 removed.** There is no test point on the antenna feed. A 1.0 mm pad on a
2.4 GHz feed is roughly 0.1–0.2 pF of shunt capacitance — the same order as C11
at 0.3 pF — so it perturbs the impedance it exists to measure. Tuning a PCB IFA
is done by soldering a coax pigtail directly to the feed trace, shield to the
adjacent ground pour, and removing it afterwards; that needs no footprint. J5
also sat 5.8 mm off the feed line, which would have hung a λ/12 stub on the
match.

### J5 — Hirose U.FL-R-SMT-1(10), antenna connector

Replaces the PCB inverted-F. See LAYOUT.md §3 for why. Verified against the
Hirose U.FL catalogue drawing: **50 Ω, DC–8 GHz**, V.S.W.R. ≤1.3 to 3 GHz,
mated height 1.9–2.4 mm nominal (2.5 mm max), **30 mating cycles**, 15.7 mg,
7.7 mm² mounting area. Footprint `Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical`.

Mated height is nothing against the 6.70 mm of clearance under the cell, and J5
sits in the y 0–11.5 band that the cell does not cover anyway.

**Buy an adhesive antenna with a U.FL plug on 1.13 mm or 1.32 mm coax** — Hirose
specify V.S.W.R. per plug/cable in their catalogue, and the U.FL-LP-068HF
(φ1.13) is the better of the two at 2.4 GHz (1.4 max vs 1.5 max at 3–6 GHz).
U.FL is rated for 30 mating cycles, so treat it as mate-once.
