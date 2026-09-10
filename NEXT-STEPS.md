> Rev A checkpoint: consolidated schematic and updated PCB match the JLC export. See [checkpoint and Rev B follow-ups](docs/rev-a-checkpoint/README.md).

> 2026-09-09 cost revision: U4 is now Sensirion SHT40-AD1F-R2. The existing SHT4x footprint, membrane handling, geometry, and legacy SHT45-named model/rule areas are retained. See [cost revision](docs/cost-reduction-2026-09-09/README.md).

> Current nRF Moisture Sensor work: [2026-09-05 review and remaining tasks](docs/design-review-2026-09-05/README.md). This supersedes older routing and unresolved-order-code notes below.

# Where this stands, and what's next

**Current state — 2026-09-04 BL54L15 migration:** U1 is 453-00001R; X2,
the discrete nRF DC/DC/RF support and the host antenna are removed. X1 and all
product GPIO assignments are retained. Routing is deliberately left for Alex.
Use [the current checklist](BOARD-FINISH-TODO.md) and
[the integration / verification record](docs/bl54l15/README.md).
Manufacturing outputs are review-only. Supply ripple, module input capacitance,
clock trim and the enclosure's incomplete preferred metal separation remain
prototype gates.

## Earlier engineering journal (historical state)

The following entries preserve prior work. Their bare-QFN, X2, AE1/R27/C29,
RF-return, routing-complete and BOM counts are superseded by the module migration.
Unrelated enclosure, PMIC, sensing and DK experiment findings remain references.


Companion to [HARDWARE.md](HARDWARE.md), [LAYOUT.md](LAYOUT.md) and [BOM.md](BOM.md).
Written at the end of the placement session.

**Schematic ERC 0 errors, 0 warnings.** The production board is physically
routed, including the RF launch and matching network; the remaining gate is the
final DRC result and review of any intentional warnings. The maintained board,
not a generator or route table, is the source of truth for all copper.

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

The one-shot generators and historical route writers are retired and fail-safe:
`tools_gen_pcb.py`, `tools_gen_sch.py`, `tools_route.py`,
`tools_finish_routes.py`, `tools_add_zones.py`, and `tools_place_fixups.py` exit
before reading or writing project data. Do not run them as part of production
work. The maintained KiCad files and the physically routed board are the source
of truth; only review/measurement helpers that explicitly write scratch output
remain in use.

---

## The board

**42.0 × 155.0 mm**, four layers, **JLC04161H-3313**, 1.6 mm nominal (see §3).

| Zone | y | |
|---|---|---|
| A antenna | 0 – 10.0 | AE1 copper radiator and all-layer keepout |
| B electronics | 10.0 – 74.0 | 34.0 mm wide, in the enclosure, solid In1.Cu |
| — SHT45 jut-out | 18.1 – 23.1 | x 34 → 42, through the side wall |
| C probe | 74.0 – 155.0 | 20 mm wide, no ground on any layer |

The maintained board now uses AE1, an integrated PCB monopole, with R27/C29
antenna tuning provisions. J5 and the external flex antenna are removed.
This geometry is provisional until RF tuning is complete. See LAYOUT.md §3.

---

## Blocking, in rough order

### 1. Routing — incomplete; antenna connected

The antenna conversion adds no DRC errors or unconnected items. The existing
board still has 11 track-width errors and 3 unconnected items; resolve them
before fabrication. The RF path is:
U1 pin 31 → L2/C6/L3/C9/L4/C11 → R27 → AE1, all on F.Cu with no RF vias; C6 returns
locally through `RF_PA_RETURN_LOCAL` under U1's VSS_PA/centre-pad tie, and C9
uses the B.Cu-only `RF_C9_RETURN_BOTTOM` return. Zone B retains the continuous
In1.Cu ground and matching cutouts; the F.Cu RF corridor remains via-free.

Do not use the retired route table to regenerate copper. Review the maintained
board in KiCad and complete the final DRC pass before release. `tools_add_zones.py`
and `tools_place_fixups.py` remain historical records/helpers only; do not run
them against the production board unless their output is first reviewed in a
scratch copy.

The remaining status is electrical verification rather than route generation:
inspect the final DRC report and resolve any intentional warnings before fab.
The stacked ground structure is deliberate: Zone B GND on F.Cu/In1.Cu, +3V3
on In2.Cu, and driven guard on the probe layers.

Watch what the DRU cannot catch. **NT1 needs no copper** — its pads physically
overlap U1 pad 32 and pad 49, so the tie is made by the land pattern; that is
what the NT1 clearance exemption in the `.kicad_dru` is for. **NT2 must stay on
B.Cu.** And the U1 centre-pad via array must not bridge RF_PA_RETURN_LOCAL to GND anywhere
except at NT1 — the nearest via is 0.345 mm from NT1's `/RF_PA_RETURN_LOCAL` pad and DRC
reports no short, so that holds.

### 1a. C6 return geometry (record)

Routing found a hard blocker. U1 pins 33 (DECRF), 34 (XC1) and 35 (XC2) all
have to escape westward, and the only corridor was the band between C6 and the
bottom pad row. `/RF_PA_RETURN_LOCAL` ran diagonally from C6.2 at (75.22, 58.5) up to pad
32 at (76.4, 60.079), straight across it. Solving the point-to-line distance
for pin 33 at x = 76.0 gives a legal 0.15 mm track only at **y ≥ 59.814 or
y ≤ 58.459** — the first is inside the pad row, the second is on the far side
of `/RF_PA_RETURN_LOCAL`. **Pin 33 had no legal escape at any width.**

The crossing is structural rather than a width problem: C6's ground pad has to
reach pin 32, and unless it sits directly under pin 32 that return path
separates pins 33/34/35 from everything below them.

**C6 is now rotated 270° at (76.10, 57.50)**, in the 0.91 mm gap between L3 and
L2, ground pad under pin 32. `/RF_PA_RETURN_LOCAL` becomes a straight climb up x = 76.35
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

**What it costs.** `/RF_PA_RETURN_LOCAL` is now squeezed between pin 33's pad at x = 76.102
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
controlled RF corridor. The 0.1565 mm width is JLCPCB's official non-coplanar
L1/L2 calculator result; coplanar ground would change the impedance. The In1.Cu
reference under the run is untouched — the stitching
generator bans vias in the whole RF corridor for the same reason.

Both new pours use **solid** pad connections, not thermal relief. Spokes cannot
resolve two-per-pad on the QFN ground pins, which
DRC reports as `starved_thermal`, and a spoke in series with a QFN ground pin
is inductance this board does not want. The cost is that GND pads are harder to
hand-solder.

### 2. Power-input architecture — retired from this board

The production board is CR2032-only. USB-C, solar, rechargeable-pack, charger,
NTC, and charge-status circuitry are not fitted and have no nets or footprints
in the production PCB. Do not place, route, or reintroduce those legacy blocks;
they belong to the separate pump-controller board.

### 3. Stackup and fab action

Order **JLC04161H-3313**, 4-layer, 1.6 mm nominal, with impedance control.
The symmetric 3313 dielectric is 0.0994 mm (εr 4.1), the 1.265 mm core is εr
4.42, and the official calculator width is **0.1565 mm** for 50 ohm
non-coplanar L1/L2. Confirm the pressed stack and impedance result on the fab
acknowledgement. See LAYOUT.md §1–2.

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

The antenna-end reliefs are retained. The new AE1 radiator fits inside the
remaining central top tongue (LAYOUT.md §3). At the probe end they forced the LED cluster to move: D3/D4 and
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

Hammond do factory milling for the first two.

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
re-discovered: a moulded gasket around the probe rather than a bead, and the
SHT45 moved off its jut-out and behind a PTFE membrane vent. That is a
different enclosure, not a modification of this one.

**Two stale notes closed by this.** LAYOUT.md §10 said the SHT45 in a sealed
box "measures the box, not the room" and wanted a membrane vent in the lid —
that stopped being true when U4 moved onto the jut-out and left the box
entirely. The production enclosure has no board-mounted external power inlet.

---

### 2. X2's pad numbering was on the wrong diagonal — fixed, and it would have killed the 32 MHz oscillator

Found while lining the 3D models up. The model was right and the footprint was
wrong.

FA-128 datasheet page 1, "External dimensions" TOP VIEW with the 2.0 mm axis
horizontal, has **#4 top-left, #3 top-right, #1 bottom-left, #2 bottom-right**,
and the "Internal connection (TOP VIEW)" inset puts the resonator between
**#1 and #3** with the note *"#2 and #4 are connected to the cover. (Please
connect to ground)"*. So the crystal terminals are the BL–TR diagonal and the
cover pads are BR–TL.

Epson's recommended land on the same page is **1.45 mm wide × 2.00 mm tall** —
0.95 mm x-centres, 1.15 mm y-centres, 0.5 × 0.85 mm pads — which our footprint
copies exactly. That land seats the part with its **2.0 mm axis vertical**, so
the pinout rotates with it:

| | #1 | #2 | #3 | #4 | crystal on |
|---|---|---|---|---|---|
| 90° CW | TL | BL | BR | TR | TL–BR |
| 90° CCW | BR | TR | TL | BL | TL–BR |

Both give the same answer, because 180° maps a diagonal to itself: **with the
2.0 mm axis vertical the crystal terminals are always TL–BR.**

The footprint had **pad 1 at BL and pad 3 at TR — the cover diagonal.** The
schematic wires pad 1 to XC1 and pad 3 to XC2, so XC1 and XC2 would have landed
on the two grounded cover pads and the actual crystal terminals would have been
tied to GND through pads 2 and 4. The oscillator would not have started.

**Nothing in ERC or DRC could see it.** All four pads exist, all four are
connected, and the two ground pads are legitimately ground. It is only visible
against the datasheet drawing, or — as it happened — by noticing that the 3D
model's index mark refused to line up.

Fixed in `tools_fix_footprints.py`, applied to both the library `.kicad_mod`
and the placed instance: the numbering rotates one position so pad 1 is the
top-left corner, which keeps 1–3 and 2–4 diagonal as the part requires. The
silk pin-1 dot moved to match, and the F.Fab rectangle — drawn 2.0 × 1.6 where
its own pads say 1.6 × 2.0 — was transposed and given its chamfer on the new
pin-1 corner. `/XC1` and `/XC2` were re-routed to the corrected pads.

**Renaming a pad does not move its net.** The net follows the piece of copper,
so the first pass left GND on pads 1 and 3 — the same defect one corner round.
The script now states the schematic's pad→net binding explicitly and enforces
it.

### 3. 3D models — current fitted parts covered

`tools_3d_models.py` is the model-assignment table used by the repair tool.
Project footprints carry the same assignments, so updating footprints from the
library does not remove their models.

| | model | rotation | why |
|---|---|---|---|
| U1 | `lib/nordic/QFN48_6X6_NOR.step` | none | Nordic QFN48 model, already Z-up |
| U2 | KiCad `Texas_RSA_VQFN-16-1EP_4x4mm….step` | none | matches the selected QEAA QFN16: 4×4 mm, 0.65 mm pitch, 2.7 mm exposed pad |
| X1 | `lib/CM8V-T1A/…​.step` | (−90, 0, 0) | vendor model, height along +Y |
| X2 | `lib/FA-128 …​.STEP` | (−90, 0, 90) | height along +Y; Z turn aligns its long axis |
| U4 | `lib/SHT45_AD1F_R2/SHT45-AD1F-R2.step` | (−90, 0, 0) | local vendor model replaces a missing KiCad-library reference |
| L10 | `lib/DFE201210U_2R2M_P2/IND_DFE201210U-2R2MP2_MUR.step` | none | supplied Murata model, already Z-up and centred |
| BT1 | `lib/CR2032-BS-6-1_C70377.step` | (0, 0, 180), Z offset +0.08 mm | Q&J visualization substitute; purchase Lian Xin CR2032-BS-6/C22363833 per the schematic and selected-holder drawing |

The similarly named downloaded nPM2100 bundle contained a 1.9×1.9 mm WLCSP
model and was removed. The selected `nPM2100-QEAA` is the 4×4 mm QFN; Nordic's
package code for the WLCSP is `CA`, not `QE`.

**The rule that makes this tractable:** KiCad's 3D frame is X = footprint X,
**Y = minus footprint Y**, Z = up. A pad at footprint local (lx, ly) sits at
3D (lx, −ly). The Nordic models confirm it — QFN48's pin-1 lead is at model
(−2.768, **+2.200**) and its pad 1 at local (−2.921, **−2.200**), the same
corner with y negated — which is why they need no rotation at all.

The two crystal models and the holder model are vendor exports with package
**height along +Y** instead of +Z, measured with cadquery rather than guessed:

```
FA-128     x -0.800..0.800 (1.600)   y 0.000..0.500 (0.500)   z -1.000..1.000 (2.000)
CM8V-T1A   x -1.000..1.000 (2.000)   y 0.000..0.600 (0.600)   z -0.600..0.600 (1.200)
BU2032     x -15.93..15.93 (31.86)   y 0.000..5.200 (5.200)   z -9.925..9.925 (19.85)
```

so they need one −90° turn about X to stand above the PCB. Verify with
`kicad-cli pcb render --side top --pivot …` rather than by eye in the GUI — it
is repeatable and it is how the FA-128 defect surfaced.

Still without models, all legitimately: J4 (Tag-Connect, no fitted body), NT1
and NT2 (net ties), and TP1–TP3 (bare pads).

---

## Verify before fab

- ~~Window-pane the QFN paste apertures~~ — **done.** Both lands were drawn
  oversize and pasted as one full-area aperture. Against the vendor package
  drawings (nRF54L15 Table 83: D2/E2 4.5/**4.6**/4.7 mm; nPM2100 Table 36:
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
- **Measure the CR2032 under realistic load.** Verify sleep current, the
  `+3V3_FDC_SW` gate, and the end-of-life voltage/pulse margin with the selected
  holder and enclosure. Record the measured capacity and leakage for the
  production cell; do not carry assumptions from a rechargeable pack into this
  board. See HARDWARE.md §3.

---

## Bring-up

### Only our board can do these

- **Tune AE1 with the enclosure, battery and realistic soil load.** Remove
  R27 for VNA isolation, trim the open end and select R27/C29 values. Verify
  radiated performance as well as S11 before freezing the geometry.
- **Check whether the jut-out perturbs the monopole.** It is an 8 mm cantilever
  5.8 mm from U1, within the antenna's near field. Unpowered FR4 with four thin
  traces, so probably very little, but measure rather than assume.
- **Trim INTCAP** on both oscillators. The register value excludes PCB stray,
  and the DK's stray is not ours — the DK is only good for rehearsing the
  procedure, not for a value.
- **Absolute sleep current** against the 500 mAh budget (§7). The DK carries
  loads we do not.

### On the nRF54L15 DK (PCA10156) — done, 2026-08-04

All four claims from HARDWARE.md §6 were exercised on the DK with a BME280 as
the bus target. Firmware, overlays and full results are in
[firmware/](firmware/README.md).

| Claim | Result |
|---|---|
| SDA and SCL must share a port (§8.8.3) | **confirmed** — `i2c22` cannot reach P0.04 |
| P0 can wake from System OFF (Table 40) | **confirmed** — real wake, `RESET_LOW_POWER_WAKE` |
| P2 cannot wake (Table 40) | **confirmed** — `-ENOTSUP`, the port will not arm |
| TWIM SCL needs a clock pin (Table 77) | **not reproducible** — see below |

**The pin assignment is unchanged.** Every rule we designed to held, so nothing
moves. The value is that three of them were previously "read a table and
believed it" and are now demonstrated — §8.8.3 especially, since a peripheral
that cannot reach its pin is not something ERC or DRC catches.

**The clock-pin rule could not be made to fail**, at 400 kHz or at 1 MHz, which
is the TWIM ceiling on this part. That is not evidence the rule is void: Table
77 is a timing-margin claim, and a room-temperature bench on jumper wire
consumes none of the margin. **P1.11 stays.** What we gained is knowing the
margin is large at our operating point, so deviating later would be a
deliberate low-risk choice rather than a blind one.

**Honest assessment of the exercise.** None of it changed the board. The prior
probability that Nordic's own tables were right was always high, and we had
already complied with all three rules, so the tests could only ever return
"yes, you were right". What it did buy, beyond the verification itself, is a
working container build, flash and console path, plus `pin-probe` for telling
`-ENODEV` apart from a loose wire — all of which real bring-up needs anyway,
and all cheaper to build against a known answer than an unknown one.

**Still to do on the DK, and not yet done:** set VDD:nRF to 3.3 V in Board
Configurator (default is 1.8 V) and take a System OFF current baseline on P6
with the PPK2. Leave SB9 closed so the external flash stays on VDD:IO and out
of the measurement. This will not give us our sleep figure — the DK carries
loads we do not — but it proves nothing is holding the SoC awake.

**Bench traps, both of which cost time here:**

- The **P1 header's 00-03 positions are parenthesized** on the silkscreen and
  are not connected without modification (P1.00/P1.01 need SB3-SB6, P1.02/P1.03
  are NFC1/NFC2 and need 0 Ω resistors). P0.00-P0.04 are not parenthesized.
  Wiring "03"/"04" on the P1 header instead of P0 lands on P1.03 (dead) and
  P1.04 (`uart20` TXD, the console).
- The **P6 jumper feeds VDD:nRF**. With it out the SoC is unpowered while the
  debugger stays alive on USB 5 V, and the failure surfaces as `nrfutil` saying
  "debug port unavailable" with no mention of power.
- Each GPIO header carries its own **`VDD:IO`** pin — buffered VDD:nRF, and a
  more convenient 3.3 V supply for a breakout than P6.
- The Zephyr console is **VCOM1**, not VCOM0.

### BTHome firmware on the DK — simulated data, 2026-08-05

The seven-task BTHome plan
([docs/superpowers/plans/2026-08-04-bthome-firmware.md](docs/superpowers/plans/2026-08-04-bthome-firmware.md))
is implemented and console-verified on the DK. Full detail, build/flash
instructions and packet layout: [firmware/bthome-sensor/README.md](firmware/bthome-sensor/README.md).

Console-verified: the product-default build (no `dev.conf`) reports
`sleeping 3600 s`; the dev build (`dev.conf`, 30 s cycle) repeats correctly
across multiple System OFF wakes, with `elapsed` climbing monotonically, the
BLE identity unchanged across resets, and `m1` reading four points above `m2`
on every cycle as the encoder's ordering test requires. The encoder's host
tests (`./tests/bthome/run.sh`) pass.

The **Button 0 escape hatch is confirmed**: held at boot it prints
`Button 0 held — staying awake so the board can be flashed.` and then stays
awake indefinitely, with no further cycles and the debug port answering on
every attempt — which a device in System OFF does not.

**Home Assistant discovery is confirmed** (2026-08-05, HA at 10.1.3.4). The
BTHome integration picked the beacon up on its own as one device, `Plant-1
6100`, at `E7:B4:88:36:61:00` — the same identity the console prints — with
five entities and no YAML:

| Entity | Reading |
|---|---|
| `sensor.plant_1_6100_battery` | 79 % |
| `sensor.plant_1_6100_humidity` | 38.75 % |
| `sensor.plant_1_6100_moisture` | 38.6 % |
| `sensor.plant_1_6100_moisture_2` | 34.6 % |
| `sensor.plant_1_6100_temperature` | 71.942 °F |

(HA also creates a sixth, disabled-by-default signal-strength entity.)

**The positional `_2` mapping lands the right way round.** The entity IDs
settle the question the device page's two identically-named "Moisture" rows
cannot: the higher reading is `…_moisture`, the lower is `…_moisture_2`, four
points apart, exactly as the encoder's ordering test requires.

Values match the console field for field. Consecutive console cycles read
`m1` 38.84 → 38.76 → 38.68 → 38.60 with `m2` pinned 4.00 below, and HA's
states tracked that same series one cycle at a time. Both moisture entities
decline monotonically across a session — `moisture_2` fell 50.6 % → 34.6 %
over the 17:00–18:45 window in a dense 30-second staircase, so HA is receiving
essentially every advertisement, not an occasional one.

That the whole session lives under a single HA device rather than accumulating
new ones is the identity work holding up across hundreds of System OFF wakes.

One trap worth knowing: **the Developer Tools → States table does not always
repaint on a websocket update.** It sat two cycles stale until the page was
reloaded, which reads exactly like missed advertisements. Reload before
concluding the beacon dropped out.

**What remains:**

- **Real sensor drivers** — needs our board. The DK has no soil-moisture,
  temperature or humidity sensors attached, so all five values stay simulated
  until then.
- **Encryption** — BTHome's packet ID becomes mandatory once encryption is
  turned on, and that counter needs to be persisted across cold-boot wakes to
  avoid rewinding on every cycle. No NVS/settings subsystem exists yet.
- **Real battery reporting** — needs an nPM2100 evaluation setup for the fuel
  gauge, plus the open question already in HARDWARE.md §5:
  confirm the NCS fuel gauge library's availability for nRF54L15 and its
  RAM/flash cost for a design that cold-boots hourly.

### PMIC bring-up — nPM2100

The nRF54L15 DK cannot validate the production PMIC path. Use an nPM2100-QEAA
evaluation setup with a CR2032-equivalent source to verify TWI access, 3.3 V
boost configuration, LDOSW gating, and the built-in active discharge of
`+3V3_FDC_SW`. Keep the I²C pull-ups on always-on `+3V3`; never gate them with
the FDC1004 supply, or the PMIC cannot be reached while the switch is off.

Before first power-on, verify R27 is fitted, C29 is initially DNP and AE1 has
no ground or other copper in its keepout. See LAYOUT.md §3 for antenna tuning.

Doing this before our board arrives also means first power-on is a hardware
bring-up rather than a hardware-and-firmware bring-up at the same time.

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
- **Legacy external-input nets are intentionally absent.** Do not restore
  `/SOLAR_PANEL`, USB, or charger connectivity to this coin-cell board.

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
  coordinates on identical layers. The duplicate markers remain a documented
  library warning; the retired generator is not part of the production flow.
