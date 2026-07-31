# Where this stands, and what's next

Companion to [HARDWARE.md](HARDWARE.md), [LAYOUT.md](LAYOUT.md) and [BOM.md](BOM.md).
Written at the end of the placement session.

**Schematic ERC 0 errors, 0 warnings. PCB DRC 0 errors.** 4 isolated-copper
warnings and 115 unconnected items remain — the sense electrodes and the Zone C
guard have no copper path to U3 until the rest of the routing lands. The one
`lib_footprint_mismatch` is J1 and is the deliberate silkscreen override.

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
| A antenna | 0 – 11.5 | copper-free on all layers but AE1 |
| B electronics | 11.5 – 74.0 | 34.0 mm wide, in the enclosure, solid In1.Cu |
| — SHT45 jut-out | 18.1 – 23.1 | x 34 → 42, through the side wall |
| C probe | 74.0 – 155.0 | 20 mm wide, no ground on any layer |

58 footprints placed (56 schematic components plus AE1 and MP1, which have no
symbols). J5 has been removed — see BOM.md.

---

## Blocking, in rough order

### 1. Routing — RF done, the rest open

Routing now lives in `tools_route.py`, which is re-runnable: it removes and
re-adds only tracks, vias and zone fill, and never touches graphics, footprints
or zone outlines. **Resolve net codes before mutating the board** — see the
comment in `net_map()`.

1. ~~RF~~ — **done.** U1 pin 31 → L2 → C6 → L3 → C9 → L4 → C11 → AE1 feed, all on
   F.Cu, no vias on any RF net, 0.36 mm (JLCPCB's own calculator — §3). Pin 31 to
   the ground-plane edge is 8.579 mm against λ/8 = 8.6 mm. `/GND_PA` is F.Cu-only
   with no vias and `/GND_C9` reaches B.Cu only, so Nordic's two grounding rules
   hold. **No stitching vias** — that rule was CPWG-specific and does not apply
   here; see LAYOUT.md §2.
2. **The SW2 loop** — SW2 → L10 → C24 → PVSS2, kept physically tiny.
3. **Sense into the probe.** The one that needs care: sense over ground is
   measured capacitance. The Zone B pour will need carving away under the run
   from U3 down to the Zone C boundary.
4. Everything else.

Watch what the DRU cannot catch. **NT1 needs no copper** — its pads physically
overlap U1 pad 32 and pad 49, so the tie is made by the land pattern; that is
what the NT1 clearance exemption in the `.kicad_dru` is for. **NT2 must stay on
B.Cu.** And the U1 centre-pad via array must not bridge GND_PA to GND anywhere
except at NT1.

### 2. Solar panel, then the pre-regulator

The only part still fully unselected. Needs **V_OC 6–12 V under indoor light** —
not at AM1.5, which is what distributor tables quote. The pre-regulator choice
(TPS62122 buck or TPS7A1650 LDO) is gated on it. The 8 × 8 mm reserve, J3, D5
and the `SOLAR_5V` net are all already on the board, so nothing blocks on this.

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
0.43–0.65 mm under the top layer, which takes the 0.38 mm trace to roughly 75 Ω.

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
corner. At the probe end the relief runs straight into the R2.0 shoulder fillet
with no straight segment between them.

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

### 5. Two enclosure openings, neither sealed

The probe slot and the SHT45 jut-out slot. Both need potting, or accept losing
the IP68 rating at those points.

The jut-out slot: **5.0 mm wide × board thickness**, centred at y = 20.6 from
the board's top edge, at **4.00–5.60 mm above the box floor**. Hammond do
factory milling.

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
- **Add centre-pad vias** under U1 pad 49 and U2 pad 33. Neither vendor footprint
  has them; Nordic's reference uses a grid.
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
- **Get the DC-bias curve for L1** from Murata SimSurfing. They publish only a
  40 °C temperature-rise rating (620 mA) and no saturation current at all.
- **Measure the cell.** Self-discharge is 74 % of the power budget and the
  1–3 %/month band spans 4.6 down to 2.1 years — still the least-known number in
  the design. The **PCM is no longer a guess**: the DW01P datasheet gives
  I_CC 3.0 µA typ / **6.0 µA max**, and at the max, runtime on the 500 mAh cell
  goes from 2.92 to **2.51 years**. No distribution is published, so measure the
  pack you actually bought. See HARDWARE.md §3.

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

## Two toolchain traps worth remembering

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
