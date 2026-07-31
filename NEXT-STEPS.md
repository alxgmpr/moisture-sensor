# Where this stands, and what's next

Companion to [HARDWARE.md](HARDWARE.md), [LAYOUT.md](LAYOUT.md) and [BOM.md](BOM.md).
Written at the end of the placement session.

**Schematic ERC 0 errors, 0 warnings. PCB DRC 0 errors.** 6 isolated-copper
warnings and 44 unconnected items remain — the sense electrodes and the Zone C
guard have no copper path to U3 until the sense traces land, and the PMIC half
of the board is still to route (§1). The one `lib_footprint_mismatch` is J1 and
is the deliberate silkscreen override.

19/19 DRU fire-tests pass. Round-trip verified after every bulk edit: board
graphics come back bit-identical, and footprint positions differ only by the
two deliberate moves in `tools_place_fixups.py`.

---

## Diagrams

`doc/enclosure-fit.png`, `doc/enclosure-corner.png` and `doc/enclosure-section.png`
show how the board sits in the box. Regenerate with
`.venv-cq/bin/python tools_encl_draw.py` — the cavity in them is the real
measured cross-section from Hammond's STEP at the height the board actually sits,
not a reconstruction from radii, which is what made the corner-relief error
visible in the first place.

---

## Read this first

**Do not run `tools_gen_pcb.py` against the current board.** The `.kicad_pcb` has
been hand-edited — the jut-out corners carry manual fillets that the generator
does not emit — and `main()` strips every drawing before redrawing, so a run
would destroy them silently. The script is kept for reference: its constants
document every dimension and its self-checks record what has to stay true.

`tools_gen_sch.py` is **still authoritative** for the schematic. Edit it and
re-run; do not hand-edit the `.kicad_sch`.

---

## The board

**42.0 × 155.0 mm**, four layers, **JLC04161H-7628** (plain — see §3).

| Zone | y | |
|---|---|---|
| A antenna | 0 – 11.5 | **ordinary board now** — J5 U.FL + ground pour |
| B electronics | 11.5 – 74.0 | 34.0 mm wide, in the enclosure, solid In1.Cu |
| — SHT45 jut-out | 18.1 – 23.1 | x 34 → 42, through the side wall |
| C probe | 74.0 – 155.0 | 20 mm wide, no ground on any layer |

61 footprints placed (60 schematic components plus MP1, which has no symbol).
AE1, the PCB inverted-F, is gone — J5 is now a U.FL receptacle feeding an
external adhesive antenna. See LAYOUT.md §3.

---

## Blocking, in rough order

### 1. Routing — 124 → 44 unconnected, 0 DRC errors

Routing lives in `tools_route.py`, which is re-runnable: it removes and re-adds
only tracks, vias and zone fill, and never touches graphics, footprints or zone
outlines. **Resolve net codes AND pad positions before mutating the board** —
`board.Remove()` invalidates both sets of wrappers. Waypoints are written as
pad references (`"U1.46"`), not coordinates, so the table survives a placement
nudge.

Two companion scripts appeared alongside it:

- **`tools_add_zones.py`** — the pours and rule areas, keyed by name so a run
  replaces its own previous copy and leaves ZoneB_GND and the hand-drawn
  outline alone.
- **`tools_place_fixups.py`** — the placement changes made after the generator
  was frozen, with the reasoning attached. Currently L1 and C6.
- **`tools_stitch_gen.py`** — generates the stitching via list by filtering a
  2.5 mm grid against the routed board. Run it *after* routing.

**Done.**

1. **RF** — U1 pin 31 → L2 → C6 → L3 → C9 → L4 → C11 → J5 (U.FL), all on F.Cu,
   no vias on any RF net, 0.36 mm. `/GND_PA` is F.Cu-only with no vias and
   `/GND_C9` reaches B.Cu only, so Nordic's two grounding rules hold.
   **C6 moved** — see §1a below, it is the one thing here that changed.
2. **GND** — a new F.Cu pour (`ZoneB_GND_F`) collects the 51 top-side ground
   pads and 109 stitching vias tie it to the In1.Cu plane. Only three pads
   needed routing: U3's, U4's and one J5 ground pad.
3. **/+3V3** — a new In2.Cu plane (`ZoneB_3V3`) over the electronics band, one
   via per pad. LAYOUT.md §1 already assigned In2.Cu the role "power / guard
   pour"; this is the power half.
4. **The nRF54L15 cluster** — DCC/DECD/DECA/FB1/L1, both crystals, RESET, and
   the five long debug runs (SWDIO, SWDCLK, SWO, SWD_RST, PMIC_INT) as parallel
   B.Cu lanes down the east side.
5. **Centre-pad via arrays** under U1 pad 49 (4×4, Nordic's pattern) and U2 pad
   33 (3×3). **Order with vias tented.**

**Still open — 44 unconnected, and they are all in the PMIC half of the board:**

| | nets |
|---|---|
| power | /VSYS (5), /VBUS_IN (4), /VBAT (2), /GND_PVSS2 (2), /SW2 (1) |
| I²C | /SDA (4), /SCL (4) |
| solar | /SOLAR_PANEL (3), /SOLAR_5V (3) |
| PMIC misc | /FDC_VDD (2), /VSET1, /VSET2, /NTC, /SHPHLD, /USB_CC1, /USB_CC2 |
| LEDs | /LED0_A, /LED0_K, /LED1_A, /LED1_K |
| sense | /SENSE1, /SENSE2 |

**The one that needs care is still sense**, and the groundwork for it is now in
place: `SenseNoGround` carves the In1.Cu plane away over the U3 → Zone C
escape, and `SenseEscape_GUARD`/`_F` fill that region with driven guard on
F.Cu, In2.Cu and B.Cu instead. What remains is the two traces themselves —
SENSE1 down the 1.7 mm left guard channel past SENSE2's electrode, SENSE2 into
its own electrode via TP2. Budget 0.375 mm of guard between SENSE1 and
SENSE2's electrode edge at the tightest point.

**The known trap in the PMIC half**, found while planning and not yet acted on:
`/SW2` runs from U2 pin 5 to L10 pad 1 and `/+3V3` from L10 pad 2 to C24 pad 1,
and as L10 is currently placed those two cross. **Rotate L10 by 180°** — the
same fix as L1, for the same reason, and there is a slot for it in
`tools_place_fixups.py`.

Watch what the DRU cannot catch. **NT1 needs no copper** — its pads physically
overlap U1 pad 32 and pad 49, so the tie is made by the land pattern; that is
what the NT1 clearance exemption in the `.kicad_dru` is for. **NT2 must stay on
B.Cu.** And the U1 centre-pad via array must not bridge GND_PA to GND anywhere
except at NT1 — the nearest via is 0.345 mm from NT1's `/GND_PA` pad and DRC
reports no short, so that holds.

### 1a. C6 moved, and it fixed an RF error that was already there

Routing found a hard blocker. U1 pins 33 (DECRF), 34 (XC1) and 35 (XC2) all
have to escape westward, and the only corridor was the band between C6 and the
bottom pad row. `/GND_PA` ran diagonally from C6.2 at (75.22, 58.5) up to pad
32 at (76.4, 60.079), straight across it. Solving the point-to-line distance
for pin 33 at x = 76.0 gives a legal 0.15 mm track only at **y ≥ 59.814 or
y ≤ 58.459** — the first is inside the pad row, the second is on the far side
of `/GND_PA`. **Pin 33 had no legal escape at any width.**

The crossing is structural rather than a width problem: C6's ground pad has to
reach pin 32, and unless it sits directly under pin 32 that return path
separates pins 33/34/35 from everything below them.

**C6 is now rotated 270° at (76.10, 57.50)**, in the 0.91 mm gap between L3 and
L2, ground pad under pin 32. `/GND_PA` becomes a straight climb up x = 76.35
and the corridor opens from y 57.7 to 59.698 — room for all three lanes.

**And the old position was wrong on RF grounds independently.** C6 is the
1.5 pF shunt on the L2/L3 node at x = 76.8. From (74.58, 58.5) its stub to that
node ran 3.02 mm, roughly 2 nH in series with the capacitor:

| | Z at 2.4 GHz |
|---|---|
| ideal 1.5 pF | −j44.2 Ω |
| with the old 3.02 mm stub (~2 nH) | +j30.2 − j44.2 = **−j14.0 Ω** |
| with the new 0.39 mm stub (~0.3 nH) | +j4.5 − j44.2 = **−j39.7 Ω** |

A 3× error in the shunt reactance is not a rounding difference — the stub was
doing more to the match than the capacitor was.

**What it costs.** `/GND_PA` is now squeezed between pin 33's pad at x = 76.102
and the `/ANT` run at x = 76.62, so it narrows from 0.4 mm to 0.2 mm over most
of its length: about 2.0 mm of 0.2 mm track, ~1.9 nH against ~1.2 nH before.
Roughly **+0.7 nH in the VSS_PA return**, traded for taking ~1.7 nH out of the
shunt branch. Both are inside the VNA session that was already budgeted.

### 1b. What the layer plan actually is now

| Layer | Zone A | Zone B | Zone C |
|---|---|---|---|
| F.Cu | ground pour | ground pour, **not** in the RF corridor | electrodes + guard |
| In1.Cu | ground plane | ground plane | **nothing** |
| In2.Cu | — | **+3V3 plane** | guard |
| B.Cu | — | signal (debug bus) | guard |

`RFPourKeepout` holds the F.Cu ground pour ≥ 1.1 mm off the x = 76.8
microstrip. That matters: W = 0.36 mm comes from the **microstrip** equation,
which assumes no coplanar ground, and ground on F.Cu 0.5 mm away would pull the
impedance down. The In1.Cu reference under the run is untouched — the stitching
generator bans vias in the whole RF corridor for the same reason.

Both new pours use **solid** pad connections, not thermal relief. Spokes cannot
resolve two-per-pad on J1's 0.6 mm USB-C row or on the QFN ground pins, which
DRC reports as `starved_thermal`, and a spoke in series with a QFN ground pin
is inductance this board does not want. The cost is that GND pads are harder to
hand-solder.

### 2. Solar — selected; U5/C30/C31 still need placing

**Panel: Voltaic Systems P126** (Adafruit 5366), 6 V 2 W ETFE, V_OC 8.59 V at
STC. **Pre-regulator: U5 = TI TPS7A1650**, fixed 5.0 V LDO, HVSSOP-8, with
C30 4.7 µF/50 V and C31 10 µF/25 V. See HARDWARE.md §4 and BOM.md.

The panel moved *outdoors* — it VHB-mounts in a window on a lead, which removed
the 200 lx constraint that had forced an amorphous panel and let crystalline
silicon win on power per area, price and durability. At 136 × 112 mm it is
larger than the whole enclosure, which is fine: a box in a plant pot is under
the foliage, the worst place in the room for a panel.

**Solar is fitted on every board.** It was briefly DNP-by-default, but the parts
are three passives and an LDO in space that was already reserved, and a populated
board is upgraded by plugging a panel in rather than by reworking. `SOLAR_DNP`
is `False` in `tools_gen_sch.py` and nothing in the schematic carries a DNP flag.

**The barrel jack is on the panel pigtail, not the board** — a CUI PJ-102AH is
11.0 mm tall against 6.90 mm clear under the cell at J3, so it would have forced
the whole solar block into the y 62–74 end band. J3 stays the 4.25 mm JST GH.

**Placed.** U5, C30 and C31 now sit in the reserve below J3 — U5 at board
(24.37–30.63, 50.75–54.25), C31 and C30 in a row above it at y 48.27–49.73. The
block is 7.3 × 6.0 mm inside the ~8 × 8 mm reserve, 0.57 mm clear of J3 at the
tightest and 2.85 mm off the board edge. **Not routed** — the solar nets are part
of the general routing still outstanding.

**Firmware, and it is the opposite of the USB path:** U5 is a 100 mA part, so do
**not** raise the VBUS input current limit when running from solar. The 100 mA
reset default is already correct there.

### 3. Stackup — resolved, and the answer changed

**Ask for `JLC04161H-7628` — plain, no suffix.** Not 7628D.

Re-read against JLCPCB's published stackup list. Three 4-layer entries have the
single 0.21040 mm prepreg under the top layer, not one: the default "No
requirement Stackup", plain `JLC04161H-7628`, and `JLC04161H-7628D`. The first
two have a 1.065 mm core and sum to **1.586 mm** — a real 1.6 mm board. 7628D has
a 1.265 mm core and sums to **1.786 mm**.

That is what the old "confirm the total thickness" question was detecting: 7628D
was never going to be 1.6 mm. All three give identical impedance because the top
dielectric is the same, so plain 7628 is strictly better — right thickness, and
it is also the cheapest and quickest option. B/C/E/F remain out: they put
0.43–0.65 mm under the top layer, which takes the trace to roughly 75 Ω.

**The RF trace is now 0.36 mm, not 0.38.** JLCPCB's own impedance calculator was
run on the exact stackup (4 layer, 1.6 mm, 1 oz / 0.5 oz, 50 Ω single-ended,
signal L1, bottom ref L2) and returns **14.12 mil = 0.3586 mm**. The old 0.38 mm
came from a hand calculation at ε_r 4.2; at JLCPCB's published 4.4 it is 48.8 Ω,
VSWR 1.024. Small, but there is no reason to carry it. Board and DRU updated.

The calculator also reports finished thickness per stackup, which is what settled
the question above: plain 7628 is **1.59 mm and flagged *Standard***, 7628D is
**1.79 mm and *Special***. See LAYOUT.md §2.

Still worth doing: **order with impedance control** so they re-solve on the real
pressed stackup, and confirm the stackup name on the acknowledgement.

### 4. ~~The board does not fit the enclosure~~ — fixed

Measured from Hammond's STEP with cadquery (`tools_encl_check.py`). The 1551WK
cavity is not a rounded rectangle: it has four corner bosses running the full
cavity height, **R4.4193 mm at the board's bottom face**, centred at
**(±35.75, ±15.75)** from the box centre. The board's old R4.5 corners were
entirely inside them — 4.32 mm of interference at all four corners.

This also resolved the drawing figures that "did not reconcile": `R4.42` is the
boss radius and `62.00 × 22.00` is the flat edge span left *between* the reliefs.
Hammond's "Maximum PCB 74.50 × 34.50" assumes the corners are scalloped.

**Fixed — at R5.0, not the R4.669 first tried.** All four corners carry a concave
relief arc centred on the boss, meeting the board edge **6.091 mm** in from each
corner. At the probe end there is a **0.409 mm flat at y = 74** between the
relief and the shoulder fillet, and the fillet is **R0.5** — see below.

**The first attempt at R4.669 did not fit, and it is worth recording why.** It was
solved against the boss circle alone. The real cavity corner is not just that
arc: an **R1.0 blend** joins each wall to the boss, and it intrudes slightly
further than the boss circle does. Measured against the *actual* cavity boundary,
R4.669 gave **−0.028 mm** — interference, not the intended +0.25 mm clearance.
Solving against the measured boundary instead gives R ≥ 4.986, so R5.0 is used.

| | cut-back | clearance to the real cavity |
|---|---|---|
| R4.669 (boss circle only) | 5.749 mm | **−0.0278 mm** — interferes |
| **R5.0 (measured boundary)** | **6.091 mm** | **+0.2624 mm** |
| R5.5 | 6.606 mm | +0.5348 mm (saturates — limited by the 0.545 mm side gap) |

Hammond's own numbers agree with the corrected figure and not the first one: their
`62.00 × 22.00` flat span on a 74.50 × 34.50 PCB implies a **6.25 mm** cut-back.
Ours is 6.091 mm on a 74.0 × 34.0 board, which scales to 6.34 mm. The old 5.749 mm
scaled to 5.999 mm and undershot it.

Verified by sampling the whole Edge.Cuts outline against the measured cavity at
both the board's bottom and top faces: **0 points outside, 0.2624 mm tightest at
the bottom face** (the worst case — the bosses taper with draft, so the top face
is looser at 0.3066 mm).

**The shoulder fillet had to shrink from R2.0 to R0.5.** The relief reaches
x = 6.091 at y = 74 and the probe edge is at x = 7.0, so there is 0.909 mm per
side for the fillet plus any flat. R2.0 and R1.0 are both impossible. R0.5 leaves
a 0.409 mm flat. Recovering R2.0 would need the probe narrowed to ~16.8 mm, which
leaves the 16 mm electrodes 0.4 mm of guard — not viable. See LAYOUT.md §9.

`ZoneB_GND` also needed its outline rebuilt: as a plain rectangle its fill came
within 0.2984 mm of the new arcs against the 0.3 mm edge rule. It now follows the
corners at R5.35.

The antenna-end reliefs were only possible because the PCB inverted-F is gone
(LAYOUT.md §3). At the probe end they forced the LED cluster to move: D3/D4 and
R25/R26 shifted from y 108.5/111 up to y 99.5/102, clear of both the relief and
the bottom-right mounting hole.

Post pattern and post height are confirmed exactly as documented — (±27.50,
±12.50), a 55.00 × 25.00 pattern, 4.00 mm tall — and the mounting holes land on
them.

### 5. ~~Three enclosure openings, none sealed~~ — decided: the box is IP54, not IP68

**The IP68 rating is given up deliberately.** Write it on the drawing. Three
openings, one sealing method, and the target is splash resistance:

| Opening | Size | Seal |
|---|---|---|
| Probe slot, end wall | 20.2 × 1.8 mm | flexible RTV silicone bead, both faces |
| SHT45 jut-out slot, long side wall | 5.0 mm × board thickness, centred y = 20.6, 4.00–5.60 mm above the floor | same |
| Solar lead, end wall | Ø3.5 mm drilled | same, with a figure-of-eight strain relief inside |

Hammond do factory milling for the first two. Drill the third yourself — it is
a round hole and not worth a tooling charge.

**Why not keep IP68.** Three separate reasons, and the first one alone settles
it:

- **Any milling voids Hammond's rating anyway.** It is a rating on the
  enclosure as supplied, with its moulded gasket and captive lid screws. Once a
  slot is cut through a wall, the number on the datasheet describes a part that
  no longer exists, whatever is put in the slot afterwards.
- **The probe slot cannot be sealed rigidly.** The probe is an 81 mm cantilever
  that gets pushed into soil, and its shoulder fillet is already down to R0.5
  because the corner reliefs took the room (LAYOUT.md §9). A hard potting
  compound at the wall would make that shoulder the stress riser for every
  insertion. It has to be a flexible bead, and a flexible bead round a
  rectangular slot is not an immersion seal.
- **The threat model is watering splash, not immersion.** The box sits in a
  plant pot indoors. IP54 covers that. Nothing about the design contemplates
  the unit being under water, and if it were, the probe is a bare capacitive
  electrode in the soil regardless.

**What it would take to keep IP68**, recorded so the option is not
re-discovered: a moulded gasket around the probe rather than a bead, a sealed
bulkhead connector for the solar lead instead of a potted pass-through, and the
SHT45 moved off its jut-out and behind a PTFE membrane vent. That is a
different enclosure, not a modification of this one.

**Two stale notes closed by this.** LAYOUT.md §10 said the SHT45 in a sealed
box "measures the box, not the room" and wanted a membrane vent in the lid —
that stopped being true when U4 moved onto the jut-out and left the box
entirely. And J1 (USB-C) adds no fourth opening: it stays service-only, reached
by opening the lid, which is what its position hard against the left board edge
already implies.

---

## Verify before fab

- ~~Window-pane the QFN paste apertures~~ — **done.** Both lands were drawn
  oversize and pasted as one full-area aperture. Against the vendor package
  drawings (nRF54L15 Table 83: D2/E2 4.5/**4.6**/4.7 mm; nPM1300 Table 36:
  3.4/**3.5**/3.6 mm) the QFN48 land was at D2 max and the QFN32 land was
  3.6068 mm, i.e. *over* its 3.6 mm maximum. Both are now at D2 nominal with a
  3×3 aperture array — U1 1.25 mm on 1.675 mm pitch, U2 0.95 mm on 1.275 mm
  pitch, both 66 % coverage, inside IPC-7093's 50–80 %. Thermal paste volume
  drops 35.1 → 22.2 mm². Verified in the exported `F.Paste` gerber: 9 flashes
  each and no full-area aperture. Fixed in `lib/footprints.pretty/` and in the
  placed instances, so a re-import stays correct.
- ~~Add centre-pad vias under U1 pad 49 and U2 pad 33~~ — **done.** U1 gets
  Nordic's 4×4 grid at 1.2 mm pitch; U2 gets 3×3 at the same pitch, because
  4×4 at 1.0 mm would put the outer annulus past the 3.5 mm pad edge. 0.3 mm
  drill on 1.2 mm pitch is 0.9 mm hole-to-hole against the 0.5 mm minimum.
  **Order with vias tented** — the paste is window-paned to 66 % coverage and
  untented vias under a thermal pad wick solder out of the joint.
- **Confirm C0 for the FA-128 with Epson — still open, now confirmed unobtainable
  from the datasheet.** `FA-128_en.pdf` was re-read end to end: the Specifications
  table gives f_nom, T_stg, T_use, DL, f_tol, f_tem, C_L, R1 and f_age, and there
  is no C0 row at all. It is half of what the Figure 17 ESR curve checks, so this
  needs an email to Epson. ESR (60 Ω max at 26–54 MHz), drive level (200 µW max,
  10 µW recommended) and the land pattern are all confirmed — see BOM.md.
- **1551WK corner reliefs — measured, and the board does not fit.** See the
  BLOCKING entry below. `R4.42` from the drawing is confirmed exactly (4.4193 mm
  measured) and `62.00 × 22.00` is the flat edge span *between* corner reliefs,
  so the drawing was self-consistent all along — it was telling us the PCB needs
  scalloped corners. The `55.00 × 25.00` post pattern is confirmed exactly.
- ~~Get the DC-bias curve for L1 from Murata SimSurfing~~ — **closed by changing
  the part.** L1 is now the **TDK MLZ1608M4R7WT000**, which publishes I_sat
  (120 mA at 50 % L drop) and I_temp (350 mA typ). The Murata published neither —
  only a 620 mA temperature-rise figure — and saturation is what matters in a
  buck. Nordic's `4.7 µH / 120 mA / ±20 % / 650 mΩ` line turns out to be the TDK
  part's datasheet row verbatim, and the nRF54L15 publishes no DC/DC peak
  current at all (§11.14). Worst-case peak through L1 is ~60 mA at maximum TX
  power, ~2× under the 120 mA half-inductance point. See BOM.md.
- **Measure the cell.** Self-discharge is 74 % of the power budget and the
  1–3 %/month band spans 4.6 down to 2.1 years — still the least-known number in
  the design. The **PCM is no longer a guess**: the DW01P datasheet gives
  I_CC 3.0 µA typ / **6.0 µA max**, and at the max, runtime on the 500 mAh cell
  goes from 2.92 to **2.51 years**. No distribution is published, so measure the
  pack you actually bought. See HARDWARE.md §3.

  **This is bench work and it cannot be closed from a datasheet, so here is the
  procedure rather than another reminder.** Two separate numbers, two separate
  measurements, and they are not the same difficulty:

  **1. PCM quiescent current — ten minutes, do it first.** Charge the pack,
  rest it an hour, then put a µA meter in series with the pack's negative
  terminal with nothing else connected. Read I_CC directly. The DW01P spread is
  3.0 µA typ to 6.0 µA max with no published distribution, and that alone moves
  projected runtime from 2.92 to 2.51 years — a 14 % swing decided by which
  part you happened to get. A DMM's µA range has enough burden voltage to
  matter here; use a meter with < 50 mV burden at 10 µA, or a shunt and an
  instrumentation amp. If the reading is above ~6 µA the pack is not a DW01P
  or it is faulty; check the marking before believing the number.

  **2. Self-discharge — weeks, and there is no shortcut.** Charge to the
  4.15 V termination this design uses (HARDWARE.md §3, not 4.2 V), rest 24 h,
  record the open-circuit voltage, then store disconnected at a controlled
  20–25 °C. Re-measure at 30 days. Then discharge at C/20 to 3.0 V and
  integrate to get the capacity actually left. Self-discharge is
  `(C_nominal − C_measured)/C_nominal` per month, minus the PCM's own draw from
  step 1 — the pack's protection board is inside the cell you are measuring, so
  subtract it or you will attribute its 26–53 mAh/yr to the chemistry.

  **What the answer changes.** `runtime = 0.95·C / (k·C + F)` with C = 500 mAh,
  k the monthly self-discharge as a fraction ×12, and F the fixed terms:

  | self-discharge | k | F = 42.8 (PCM typ) | F = 69.4 (PCM max) |
  |---|---|---|---|
  | 1 %/month | 0.12 | 4.62 yr | 3.55 yr |
  | 2 %/month | 0.24 | 2.92 yr | 2.51 yr |
  | 3 %/month | 0.36 | 2.13 yr | 1.92 yr |

  So the two measurements together span **1.92 to 4.62 years** — a factor of
  2.4 on the headline number, and nothing in the layout comes close to
  mattering that much. Do step 1 today; step 1 alone narrows the table to one
  column.

---

## Bring-up

- **Tune the antenna with the enclosure fitted and a realistic soil load.** The
  matching values are Nordic's but there is no Nordic antenna — the QFAA
  reference layout contains none — so treat them as a starting point, not a
  known-good position. Budget a VNA session.
- **Check whether the jut-out perturbs the IFA.** It is an 8 mm cantilever
  5.8 mm from U1, within the antenna's near field. Unpowered FR4 with four thin
  traces, so probably very little, but measure rather than assume.
- **Trim INTCAP** on both oscillators. The register value excludes PCB stray.
- **Verify `BUCKnPWMSET`.** A buck left in forced PWM draws 4.0 mA against
  800 nA — that alone would end the power budget.
- **Re-apply the VBUS current limit on every boot.** It reverts to 100 mA on any
  reset or cable event.

---

## Known loose ends

- **Split enclosure STEP files do not render in `kicad-cli`.** Geometry and
  assembly positions verified correct by bounding box; three export variants
  tried (AP214, AP203, both extensions, explicit MM units) and all load without
  error and draw nothing, while Hammond's combined file renders fine.
  `ENCL_SPLIT = False` is the default so the viewer works. Worth one try in the
  GUI 3D viewer — a different code path.
- **The enclosure 3D model does not show either milled slot**, so the fit check
  is less useful than it looks.
- **No 3D model for NT3.** It is a net tie and does not need one. X2's is now
  attached (`lib/FA-128 32.0000MF10Z-AJ0.STEP`) but its orientation has not been
  checked in the 3D viewer.
- **`/SOLAR_PANEL` is a single-node net** (J3.1) and stays that way until the
  pre-regulator lands on the board.

---

## Toolchain traps worth remembering

- **`insideArea()` is true for a ZONE that merely OVERLAPS the area.** Not for
  the part that intersects — for the whole zone. A relaxing clearance rule
  conditioned on `A.insideArea('X')` therefore catches any pour that crosses X
  anywhere, and through it every item on the board. `ZoneB_GND_F` spans the
  electronics band and crosses six of the seven `FinePitchFanout` windows, so
  the first version of that rule dropped the ground pour's clearance to
  0.15 mm **everywhere** — 97 violations, all at coordinates nowhere near a
  QFN. The fix is `&& A.Type != 'Zone' && B.Type != 'Zone'`, and
  `tools_dru_test.py` now carries a `fanout_scope` case that fails if the
  exemption escapes its windows again.
- **A keepout masks the rule under test.** KiCad reports one
  `items_not_allowed` per item, so if injected geometry lands inside a rule
  area, the keepout fires and the rule you were testing never appears. Two
  fire-tests had been sitting inside `SHT45_Jut` doing nothing. Injection
  geometry has to be checked against the board it is injected into, and the
  board changes.

## Two more toolchain traps

- **DRU rules are last-match-wins.** This had silently disabled *every* width
  rule in the file — `Fab minimum track` matches every track at 0.127 mm and sat
  at the bottom, overriding `Power track width`, `Charge path width` and
  `Switch node width`. Caught by injecting a 0.3 mm track on a Power-class net
  and getting no violation. Fabrication floors now sit **above** the specific
  rules. Any new rule needs an injection test, not a read-through.
- **Both Nordic QFN footprints carry their pin-1 marker twice**, at identical
  coordinates on identical layers. `tools_gen_pcb.py` strips the duplicates at
  load time rather than editing the vendor files — if you stop using the
  generator, expect the silkscreen-overlap warnings back.
