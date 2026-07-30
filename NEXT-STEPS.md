# Where this stands, and what's next

Companion to [HARDWARE.md](HARDWARE.md), [LAYOUT.md](LAYOUT.md) and [BOM.md](BOM.md).
Written at the end of the placement session.

**Schematic ERC 0 errors, 0 warnings. PCB DRC 0 errors.** The 4 remaining DRC
warnings and 127 unconnected items are all "nothing is routed yet" — the sense
electrodes and the Zone C guard have no copper path to U3 until routing lands.

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

**42.0 × 155.0 mm**, four layers, JLC04161H-**7628D**.

| Zone | y | |
|---|---|---|
| A antenna | 0 – 11.5 | copper-free on all layers but AE1 |
| B electronics | 11.5 – 74.0 | 34.0 mm wide, in the enclosure, solid In1.Cu |
| — SHT45 jut-out | 18.1 – 23.1 | x 34 → 42, through the side wall |
| C probe | 74.0 – 155.0 | 20 mm wide, no ground on any layer |

57 components placed, 508 mm² of courtyard in 2125 mm² of Zone B.

---

## Blocking, in rough order

### 1. Routing

Nothing is routed. Order matters:

1. **RF first, while there is freedom.** Pin 31 → the matching chain → the
   antenna feed is ~8.2 mm, and λ/8 at 2.4 GHz in FR4 is 8.6 mm — it is at the
   limit. Stitch at the full ≤3 mm density along it. No vias in the path.
2. **The SW2 loop** — SW2 → L10 → C24 → PVSS2, kept physically tiny.
3. **Sense into the probe.** This is the one that needs care: sense over ground
   is measured capacitance. The Zone B pour will need carving away under the run
   from U3 down to the Zone C boundary.
4. Everything else.

Watch two things the DRU cannot catch: **NT1 must end up under the U1 centre
pad** and **NT2 on B.Cu**, and the U1 centre-pad via array must not bridge
GND_PA to GND anywhere except at NT1.

### 2. Solar panel, then the pre-regulator

The only part still fully unselected. Needs **V_OC 6–12 V under indoor light** —
not at AM1.5, which is what distributor tables quote. The pre-regulator choice
(TPS62122 buck or TPS7A1650 LDO) is gated on it. The 8 × 8 mm reserve, J3, D5
and the `SOLAR_5V` net are all already on the board, so nothing blocks on this.

### 3. Confirm the stackup with JLCPCB

Two questions, one order:

- **Ask for `JLC04161H-7628D` by name.** It is the only 4-layer 7628 variant with
  a single 0.21040 mm prepreg under the top layer; the others put 0.43–0.65 mm
  there, which takes the 0.38 mm RF trace from 50 Ω to roughly 75.
- **Confirm the total thickness.** The published 7628D layer sum comes to
  1.786 mm, not 1.6. If 7628D is not available at the target thickness we get
  pushed onto 7628E, and the trace has to go to roughly 0.82 mm.

### 4. Two enclosure openings, neither sealed

The probe slot and the SHT45 jut-out slot. Both need potting, or accept losing
the IP68 rating at those points.

The jut-out slot: **5.0 mm wide × board thickness**, centred at y = 20.6 from
the board's top edge, at **4.00–5.60 mm above the box floor**. Hammond do
factory milling.

---

## Verify before fab

- **Window-pane the QFN paste apertures.** Both `QFN48_6X6_NOR` and
  `QFN32_5X5_NOR` have a single full-area aperture on the thermal land — 22.1 mm²
  and 13.0 mm². Both lands are also drawn at D2 *max* rather than nominal.
- **Add centre-pad vias** under U1 pad 49 and U2 pad 33. Neither vendor footprint
  has them; Nordic's reference uses a grid.
- **Confirm C0 for the FA-128 with Epson.** Not published, and it is half of what
  the Figure 17 ESR curve checks.
- **Confirm the 1551WK corner reliefs** against Hammond's STEP. The drawing's
  `62.00 × 22.00` and `R4.42` do not reconcile cleanly with the `63.88 × 23.88`
  cover-screw bosses; the `55.00 × 25.00` post pattern is unambiguous and is what
  is drawn.
- **Get the DC-bias curve for L1** from Murata SimSurfing. They publish only a
  40 °C temperature-rise rating (620 mA) and no saturation current at all.
- **Measure the cell.** Self-discharge is 74 % of the power budget and the
  1–3 %/month band spans 4.6 down to 2.1 years. The PCM's quiescent current is
  another 16 % — more than the whole nRF+PMIC sleep draw.

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
- **No 3D model for X2 or NT3.** X2's would come from Epson; NT3 is a net tie and
  does not need one.
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
