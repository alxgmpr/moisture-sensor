> 2026-09-09 cost revision: U4 is now Sensirion SHT40-AD1F-R2. The existing SHT4x footprint, membrane handling, geometry, and legacy SHT45-named model/rule areas are retained. See [cost revision](docs/cost-reduction-2026-09-09/README.md).

# Layout & RF Constraints

**2026-09-04: BL54L15 routing handoff.** Sections 2–3 and
[the integration record](docs/bl54l15/README.md) supersede all older bare-SoC RF
geometry and RF completion claims below. The board is not ready for fabrication.

Companion to [HARDWARE.md](HARDWARE.md). Everything here is encoded where it can
be: stackup in `nrf-moisture-sensor.kicad_pcb`, rules in
`nrf-moisture-sensor.kicad_dru`, net classes in the project file.

---

## 1. Stackup

Retain the four-layer stack for the sensing guard, solid module/PMIC ground
and existing enclosure thickness. The module removes the host RF feed and its
controlled-impedance fabrication requirement.

**JLC04161H-3313, 1.6 mm nominal:**

| Layer | Material | Thickness | ε_r | Role |
|---|---|---|---|---|
| F.Cu | copper | 0.035 mm | — | signal, sense electrodes, ground outside antenna keepout |
| dielectric 1 | prepreg 3313 | **0.0994 mm** | **4.1** | top signal-to-ground dielectric |
| In1.Cu | copper | 0.0152 mm | — | **GND** under electronics; sense/SHLD on probe |
| dielectric 2 | core | **1.265 mm** | **4.6** | |
| In2.Cu (`GND-SHLD`) | copper | 0.0152 mm | — | **GND** beneath electronics; sense/SHLD on probe |
| dielectric 3 | prepreg 3313 | **0.0994 mm** | **4.1** | symmetric bottom dielectric |
| B.Cu | copper | 0.035 mm | — | signal / sense electrodes / guard |

### Order note

At eventual fabrication select **JLC04161H-3313**, 4-layer, 1.6 mm nominal, with
the symmetric construction below. Confirm the pressed stack. There is no
remaining 50 Ω host RF route requiring an impedance coupon.

### JLCPCB material parameters

| | |
|---|---|
| 3313 prepreg ε_r | **4.1** |
| Core ε_r | **4.6** |
| Solder mask ε_r | 3.8 |
| Mask above trace / above substrate | 0.6 mil (0.01524 mm) / 1.2 mil |
| Etch taper | **trace top width = base width − 0.7 mil** (0.01778 mm) |
| Outer copper 1 oz | 0.035 mm |
| Inner copper 0.5 oz | 0.0152 mm |

The dielectric and copper thicknesses remain unchanged from the existing board.

---

## 2. Module placement and ground

U1 is Ezurio **453-00001R**. Its local origin is (72,54) mm, rotation 90°.
The 14 × 10 mm body occupies x=72..82, y=40..54 mm; its antenna end is flush
with the board's y=40 edge and centered on the 34 mm board width. The module's
pin 1 is at (81.497,42.2). Use the local land pattern; do not mirror it.

The host RF antenna, matching network, isolated RF returns and controlled-
impedance feed are deleted. No 50 Ω host route or RF net class remains. Retain
the existing four-layer 1.6 mm stack for the enclosure and sensing design;
the former RF impedance calculation is retired.

In1.Cu remains solid GND under the non-antenna module body. All four GND lands
have nearby vias; vias under the module are tented. Only the intended LGA lands
may expose copper beneath the module. Keep a continuous plane through the
narrow pin-1 ground strip; do not route signals through the antenna keepout.

See the [current zone simplification](docs/zone-simplification/README.md) for the current
non-overlapping zone boundaries and validation.

## 3. Integrated antenna keepout and enclosure clearance

The BL54L15 antenna rule area prohibits tracks, pads, vias and copper pours on
**F.Cu, In1.Cu, In2.Cu and B.Cu**. It follows Figure 11's hatched region:
module-local x9..14, y0..8.5, extended toward local negative y by 15 mm.
On this rotated board the keepout is x57..80.5, y39..45, with the existing
pad-39 notch. The lower ≥15 mm dimension does not establish another hatched
copper exclusion. Ground may extend to the right of x80.5; the land-row
strip is intentionally preserved. Pad 39 touches the nominal drawing boundary
by 0.025 mm; the rule area follows a 0.026 mm notch at that exact vendor land,
not a general copper exception. See the dimensioned mapping and source drawing
in [the integration record](docs/bl54l15/README.md).

Keep metal screws, wiring, shielding and enclosure coatings out of that area.
Use nylon antenna-end fasteners. The unchanged Hammond enclosure and coin-cell
holder limit metal spacing: the antenna region is about 25.5 mm from the holder's
nearest body edge. This does **not** meet all Ezurio preferred 30/40 mm metal
clearances. It is an explicit unresolved enclosure RF constraint; range/packet
loss and radiated testing with installed cell, closed lid, screws and soil are
required. A DRC pass does not establish antenna performance. No host matching
positions are retained because this variant has no external RF feed.

C3 and X1 sit immediately behind U1, with hot-air access from the board edge.
SHT45 remains on its right-side jut, roughly 18 mm from U1's body. BT1 remains
roughly 16.5 mm behind the module body. Shield the sensor/PTFE membrane during
module assembly and use a measured thermal profile; see assembly notes.

## 4. Ground plane strategy — the board is zoned, not uniformly poured

The instinct to flood every layer with ground is wrong on this board. It breaks
both the antenna and the moisture measurement. Think of the stake as three zones
along its length:

```
┌──────────────────────────┐
│  ZONE A - ANTENNA        │  module antenna; no host copper beneath
│  (top of stake)          │  all-layer copper keepout
├──────────────────────────┤
│  ZONE B - ELECTRONICS    │  solid In1.Cu ground, unbroken
│  PMIC, MCU, RF, SHT45    │  RF section at the top, adjacent to Zone A
│                          │  switchers at the BOTTOM, away from RF
├──────────────────────────┤
│  ZONE C - PROBE          │  NO ground plane at all
│  sense electrodes+guard  │  In2.Cu / B.Cu carry the driven guard instead
│  (into the soil)         │
└──────────────────────────┘
```

**Zone A**: BL54L15 antenna area at board-local y=0..5 mm, with the
manufacturer land-row strip and asymmetric keepouts specified in §3.

**Zone B**: In1.Cu (`GND`) and In2.Cu (`GND-SHLD`) provide ground references
for the front and bottom routes. The shared outer/In2 ground rectangle ends at y=106.9, before the driven
shield escape at y=107.1; it follows the antenna keepouts at the top. Existing ground vias
join both planes. Add local return stitching as final signal routing is completed.
+3V3 uses a 0.4 mm bottom trunk with front-layer load connections. See the
[ground-plane routing handoff](docs/in2-ground/README.md).

**Zone C**: no ground beneath the electrodes. Two 0.9 mm wide In1 ground fingers extend to y=112.55 for D8/D9 ESD returns, above the first electrode. Their additional adjacent-layer shield overlap is approximately 3.5 pF; fringing is additional. See §5.

---

## 5. Capacitive front end

### Why Zone C has no ground plane — the numbers

The FDC1004's shield driver is rated **400 pF maximum** (SNOSCY5, DRV). The
guard pour's capacitance to any nearby ground is what loads it.

Parallel-plate estimate, `C/A = ε₀ε_r/d`:

| Guard placement | d | C per area | Area to hit 400 pF |
|---|---|---|---|
| F.Cu guard over In1.Cu ground | 0.0994 mm | 3.64 × 10⁻⁷ F/m² | **11.0 cm²** |
| In2.Cu guard over In1.Cu ground | 1.265 mm | 2.86 × 10⁻⁸ F/m² | 140 cm² |

A probe 2 cm wide by 10 cm long is 20 cm² of guard — **right at the limit** if
there is ground plane under it. Delete the ground from Zone C and the guard's
capacitance is dominated by fringing and coupling to the environment. Wet conductive soil across a thin coating can still produce a large load.

Ground near a *sense* trace is worse still: it is measured capacitance, so it
directly consumes CAPDAC range and couples in noise. Keep ground away from the active electrodes where practical. The DRU permits
0.2 mm sense-to-Power clearance so deliberate ESD return routing is possible.

### Electrode design targets

From the FDC1004 electrical table:

| Constraint | Value | Consequence |
|---|---|---|
| Input conversion range | ±15 pF | the wet↔dry *swing* must fit in this |
| CAPDAC offset range | 0 … 96.9 pF | nulls the electrode's standing capacitance |
| Max input offset capacitance | 100 pF/channel | hard ceiling on total C at CIN |
| Shield drive | 400 pF | caps guard pour area |
| Excitation | 25 kHz, 2.4 V_pp | |

**Design the electrode for roughly 10–30 pF dry.** CAPDAC nulls the standing
value; the ±15 pF window then has to cover the full dry-to-saturated swing.
Too large an electrode and the swing clips; too small and you lose resolution.
Exact capacitance needs either simulation or a prototype — plan to trim the
electrode geometry on the first spin.

### Use SENSE2 as an above-soil reference — this is why it is wired

TI's liquid-level application (§7.1.1) uses a ratiometric measurement: a level
electrode plus a *reference environmental* electrode, so the ratio cancels
effects that are not the thing being measured.

The soil analogue, which the schematic is already wired for:

- **SENSE1 (CIN1)** — the soil electrode, in the pot
- **SENSE2 (CIN2)** — an identical electrode **above the soil line, in air**

Report the ratio rather than the raw value. This cancels a large part of the
common-mode drift from temperature, humidity and supply that would otherwise
masquerade as a moisture change — complementing, not replacing, the SHT45
temperature compensation in HARDWARE.md §5.

### Guard geometry

- **SHLD1 and SHLD2 share the single-ended excitation** in the selected measurement mode. The shared SHLD net requires single-ended measurements; do not configure hardware differential CIN1–CIN2 measurements with the outputs tied together.
- Guard trace on **both sides** of every sense trace, gap **0.2 mm** — tight
  coupling is the entire point, so this is a minimum-clearance rule, not a
  keep-away.
- Guard pour on the layer **directly beneath** each sense trace, so the sense
  net sees guard in every direction and never sees ground.
- Guard is driven by SHLD. Never substitute ground for it.
- Keep sense traces short; every millimetre adds standing capacitance that eats
  CAPDAC range.

---

## 6. Switching nodes vs the measurement

The exposed switching aggressor is **nPM2100 SW**. The nRF DC/DC loop is now internal to U1; do not recreate it on the host.
Both are in the `SWITCH` net class.

The FDC1004 excites at 25 kHz and detects narrowband, so direct in-band coupling
is unlikely. The real risk is rectification and intermodulation at the very
high-impedance sense node, which lands as a DC offset that looks exactly like a
moisture change.

Enforced in the DRU:

| Rule | Clearance |
|---|---|
| SENSE ↔ SWITCH | **3 mm** |
| SHIELD ↔ SWITCH | 2 mm |
| SENSE ↔ RF | 2 mm |

Plus, by hand:

- Keep the PMIC at the **bottom** of Zone B and the module antenna at the
  **top**, and the FDC1004 near the Zone C boundary but shielded from both.
- Keep the nPM2100 input loop compact: protected VBAT/C21/C22 → L10 → U2.SW → PVSS. Keep C23/C24 close to VINT/PVSS. The nRF DC/DC loop is inside U1.
  are the loops that radiate. Short and fat, per the DRU's 0.5 mm minimum.
- Run a ground barrier between the switchers and anything sense-related.

**Firmware has a free lever here.** Nothing forces the radio, the buck's PWM
burst and the capacitance conversion to happen simultaneously. Sequence the wake
as: force PWM → settle → convert → back to Auto → *then* advertise. See
HARDWARE.md §1 and §5 — the PSRR argument for forcing PWM during conversion, and
the fact that the wake cycle is 0.6 % of the power budget, mean you can afford to
serialise everything.

---

## 7. Net classes

Defined in the project file; the DRU keys off them.

| Class | Nets | Track | Clearance |
|---|---|---|---|
| **SENSE** | /SENSE1, /SENSE2 | 0.25 mm | 0.50 mm |
| **SHIELD** | /SHLD | 0.30 mm | 0.20 mm |
| **SWITCH** | /SW, /DCC | 0.50 mm | 0.30 mm |
| **Power** | GND, VBAT, /VINT, +3V3, /+3V3_FDC_SW | 0.40 mm | 0.25 mm |
| Default | everything else | 0.20 mm | 0.20 mm |

There are no external-input rails on the production board. The low-current
CR2032 VBAT rail follows the 0.40 mm Power-class rule so it can enter the
required bypass network without manufacturing-rule conflicts.

---

## 8. Component-specific keepouts

### SHT45 on a jut-out, outside the enclosure

The sensor leaves the box entirely on a tab through the long side wall, so it
reads outside air rather than the inside of a sealed enclosure. This replaces
the earlier routed thermal island, which isolated the sensor from the *board*
but left it breathing the box.

| | |
|---|---|
| Tab | x 34.0 → **42.0**, y 18.1 → 23.1 (**5.0 mm** wide) |
| Wall passage | x 34.46 → 37.00 (0.46 mm gap + 2.54 mm wall) |
| U4 | (39.8, 20.6) — **1.58 mm proud** of the wall outer face |
| Board overall | **42.0 × 155.0 mm** |

Board is 34.0 wide centred in a 34.92 mm interior, so there is 0.46 mm of gap
each side and the wall runs 34.46 → 37.00. The maintained board geometry keeps
U4 beyond 37.00 — otherwise the sensor sits *in* the wall rather than outside it.

**Enclosure modification required.** A milled slot in the long side wall,
**5.0 mm wide × board thickness**, centred at y = 20.6 from the board's top
edge, at **4.00–5.60 mm above the box floor** (the board sits on the 4.00 mm
posts). Hammond do factory milling. This is a second opening on top of the probe
slot, and it is not sealed — pot it or accept the loss of IP rating there.

The tab keeps a `SHT45_Jut` rule area that bans pour, so it carries only the
four traces and no ground fill. The die keepout from datasheet §5.3 stays as it
was. The tab is clear of the cell, and the ground pour stops at x = 33.7 so no
plane copper reaches it.

**SHT45 — no copper underneath.** Datasheet §5.3: *"Soldering of the central die
pad, as well as an exposed copper pad underneath it, is not recommended... due to
it acting as a heat sink which prevents the heater from functioning according to
its specifications,"* and *"there shall be no copper under the sensor other than
at the pin pads."*

The footprint (`..._SHT4x_NoCentralPad`) already omits the die pad. You must
*also* keep the ground pour out from under it — draw a rule area on **User.3
(NoCopperSHT45)**.

Mount it in the vented part of the enclosure with airflow to the sensor opening,
above the soil line.

---

## 9. Board outline and enclosure

The production outline is maintained in `.kicad_pcb`; the retired generator is
fail-safe and must not be used to redraw it.

### Enclosure — Hammond 1551WK

IP68 polycarbonate. From the Hammond 1551WKBK drawing (rev 31.08.2023):

| | |
|---|---|
| External | 80 × 40 × 22 mm |
| Inside | 74.92 × 34.92 × **17.30** mm |
| Maximum PCB | 74.50 × 34.50 mm |
| Internal #2 posts | 55.00 × 25.00 mm pattern, 4.00 mm tall |

The 17.30 mm internal height is the constraint that sizes everything else — see
"height budget" below. Note the whole 1551 family is 20 mm external / 16.00 mm
internal; only the W variants get to 17.30.

### Board

**34.0 × 155.0 mm.** The in-enclosure section is 74.0 × 34.0, i.e. 0.25 mm inside
Hammond's stated maximum on every side, with R4.5 corners and four Ø2.6 mounting
holes at (4.5, 9.5), (29.5, 9.5), (4.5, 64.5), (29.5, 64.5).

| Zone | y | Notes |
|---|---|---|
| A antenna | 0 – 5.0 | BL54L15 antenna; all-layer keepout |
| B electronics | 5.0 – 74.0 | 34.0 mm wide, solid In1.Cu outside keepouts |
| C probe | 74.0 – 155.0 | 20 mm wide, no ground on any layer |

Soil line at board-local y=115, so the module antenna region is 110–115 mm
above it. Insert depth 40 mm. SENSE2 (air reference) at y 82–112 and SENSE1
(soil) at y 119–149 are both 16 × 30 mm — identical geometry is what makes the
ratiometric measurement in §5 cancel anything.

The probe leaves through a slot in the box end wall.

**Shoulder fillets are R0.5, not the R2.0 originally drawn.** The corner reliefs
(§9 below and NEXT-STEPS.md §4) reach board x = 6.091 at y = 74, and the probe
edge is at x = 7.0 — leaving **0.909 mm** per side for everything at the shoulder.
R2.0 needs 2.0 mm of that and R1.0 needs 1.0 mm, so both are geometrically
impossible once the enclosure's corner bosses are cleared. R0.5 leaves a
**0.409 mm flat** at y = 74 between the relief and the fillet.

This is a real reduction in stress relief on an 81 mm cantilever that gets pushed
into soil, and it is the price of the board fitting the box at all. The only way
to get R2.0 back is to narrow the probe to about **16.8 mm**, which leaves the
16 mm electrodes only 0.4 mm of guard either side — not viable. If the shoulder
turns out to crack in service, narrowing the electrodes is the lever, not the
fillet.

### No sharp corners anywhere on the outline

The whole Edge.Cuts loop is tangent-continuous — **36 elements, 14 lines and
22 arcs, zero sharp vertices**. FR4 cracks from sharp corners, the router dislikes
them, and the probe is an 81 mm cantilever pushed into soil, so every angular
junction is filleted.

Twelve vertices needed it, all convex:

| where | turn | fillet |
|---|---|---|
| 6 × corner relief meeting a straight board edge | 75.52° | R1.0 |
| 2 × corner relief meeting the shoulder flat | 75.52° | R0.25 (the flat is only 0.409 mm) |
| 2 × probe spear shoulder | 49.40° | R0.5 |
| 2 × probe tip | 40.60° | R0.5 |

Rounding a *convex* corner removes material, so the edge moves away from the
enclosure wall and clearance can only improve — measured, it went from
**0.2624 mm to 0.3476 mm** at the board's underside. 1.713 mm² of board was
removed in total.

Regenerate with `.venv-cq/bin/python tools_round_corners.py`. It detects sharp
vertices by comparing incoming and outgoing tangents rather than filleting
everything, so the jut-out fillets, the shoulder fillets and the relief joins that
are already tangent are left untouched.

### Height budget — the thing that bit

Board on the 4.00 mm posts: 4.00 + 1.6 (PCB) leaves **11.70 mm** to the lid.
The selected Lian Xin CR2032-BS-6 holder has a 5.5 mm height, leaving about
**6.2 mm** to the enclosure ceiling. Preserve its part-specific stepped courtyard
and installed-cell clearance: 31.9 mm overall terminal span, 22.2 × 16 mm central
plastic region, and 20.2 mm cell diameter. See the [selected-holder drawing and
model limitations](lib/footprint-sources/CR2032-BS-6.md); the detailed Q&J model
is a visualization substitute, not the purchasing specification.

**Mounting screws.** Use nylon #2 fasteners at the antenna end. Keep metal
out of the antenna region and validate the actual enclosure configuration (§3).

### Placement

The authoritative module placement is in §2 and the actual PCB. The retired
board/schematic generators must not overwrite it. The power, battery, debug,
SHT45 and probe geometry was preserved during migration.

| Feature | Absolute PCB position / extent (mm) |
|---|---|
| U1 body | x72..82, y40..54; 90° |
| C3 | (72.7,56.5) |
| X1 | (76.625,56.3) |
| R1 / C13 | (84.5,55.5) / (82.8,56.5) |
| Battery / PMIC / sensors | Existing placements retained |

**Probe electrodes** are filled zones on all four copper layers — SENSE1 and SENSE2, each
16 × 30 mm per layer. Four solid-connected through vias per electrode join its layers. SHLD surrounds both electrodes on every layer, including a closed guard across the lower electrode’s tip end. No shield or ground plane lies between the stacked sense areas. The new ESD ground fingers add 8.721 mm² of F.Cu-to-In1 overlap and 8.902 mm² of In2-to-In1 overlap, about 3.5 pF combined before fringing. External soil/coating coupling must be included against the 400 pF driver limit.

The nPM2100 local power layout and sensing constraints below remain applicable.

## 10. Open items

- The enclosure target is IP54 after accounting for the probe and SHT45
  openings. Use a strain-relieved capillary barrier at the probe slot, mask the
  SHT45 membrane during coating, and use fully cured neutral-cure sealants.
- Confirm the 1551WK corner-relief geometry and the Ø2.6 hole pattern against
  Hammond's STEP model before fab. The drawing's `62.00 × 22.00` and `R4.6` are
  ambiguous at the resolution published; `55.00 × 25.00` is unambiguous and is
  what is drawn.
- Complete the module routing and qualify antenna enclosure clearance and VDD
  ripple as recorded in docs/bl54l15/README.md.

### Confirmed against Nordic's nPM2100 guidance

The local power block follows the nPM2100 reference topology and placement
priority rather than copying development-board coordinates. It confirms:

- **solid, unbroken inner ground plane** under the PMIC, with local return vias
  at the regulator and post-route stitching generated by KiCad's via-stitching
  zone tool
- local power distribution that preserves the signal reference planes
- SW → L10 → protected VBAT, with C23/C24 on VINT and C21/C22 on VBAT. L10 pad 2 and copper routing are connected to VBAT; current connectivity and DRC pass.

The current Zone B implementation uses both inner layers for ground and routed
power on the outer layers. This board-specific choice replaces the earlier
In2 power plane. Broader stitching remains part of final routing review.

### Comparison with TI's FDC1004EVM (SV601093B)

TI's evaluation board uses a different backing geometry:

- the sense electrode is a **solid filled area on the top layer**
- the **guard is a solid plane directly beneath it on the opposite layer**
- guard copper also **rings the electrode on its own layer** across a narrow gap

The current board differs from that EVM: it uses connected sense copper on all four layers and a surrounding SHLD guard on every layer. Both external faces sense the environment; the inner copies do not multiply sensitivity by four. See [the 9 September review](docs/probe-review-2026-09-09/README.md) for coating, range and protection limits.
- Electrode geometry: simulate or prototype for 10–30 pF dry with a swing inside
  ±15 pF.
- The module has no QFN exposed-pad paste array. Its 39 LGA lands use the
  manufacturer pattern. Keep existing U2 thermal vias tented.
- Current routing and warning counts are in docs/bl54l15/verification.md;
  older bare-QFN completion claims are retired.

### Two things worth knowing about the toolchain

- **DRU rules are last-match-wins, and that had silently broken every width
  rule.** `Fab minimum track` matches *every* track at 0.127 mm, and it sat at
  the bottom of the file — so it was overriding `Power track width`,
  `Charge path width` and `Switch node width`, all of which are stricter. Caught
  by injecting a 0.3 mm track on a Power-class net and getting no violation at
  all. The fabrication floor now sits **above** the specific width rules, and
  `BUCK2 power ground` sits **below** `Power track width` so the stricter of the
  two wins. Re-verified by injection.
- **DRU rules are last-match-wins.** For a given constraint type the last rule in
  the file that matches takes precedence, so the exemptions at the bottom of the
  `.kicad_dru` must stay below the broad fabrication minimums. Put them above and
  the minimums override them and the exemption silently does nothing — which is
  how the VSS_PA net-tie exemption failed the first time.
- The retired bare-SoC library and audit notes remain historical references.
  Current warning counts and affected footprints are listed in
  docs/bl54l15/verification.md.

## Test-point additions — 7 September 2026

Fourteen 1 mm front-side pads, TP4–TP17, provide labeled power, bus, interrupt, reset and GPIO access. The new diagnostic branches use front and In2 copper; seven ground stitches moved locally, with existing functional tracks and antenna/probe keepouts retained. [Map, coordinates and verification](docs/testpoints-2026-09-07/README.md).

## Probe revision — 9 September 2026

D8/D9 now clamp CIN1_PROTECTED/CIN2_PROTECTED to GND, on the chip side of R30/R31. The existing 5.1 kohm resistors remain provisional: TI recommends input RC much less than 1 µs. Four-layer electrodes and the closed tip guard need fresh wet/dry calibration and coating qualification; the previous front-only simulation and coating target do not qualify this geometry. See [review and verification](docs/probe-review-2026-09-09/README.md).


### Dedicated FDC bus routing handoff — 2026-09-09

U1.22 (P1.05) is /FDC_SDA; U1.23 (P1.04) is /FDC_SCL. Route to U3.10 and
U3.9 respectively and to R36.2/R37.2. R36.1/R37.1 need +3V3_FDC_SW. The two
0402 pull-ups are initially placed at (75.0, 103.7) and (77.0, 103.7) mm;
adjust placement for the final route. The old five FDC-only shared-bus spur
segments have been removed. No new tracks or vias were added.

Consider escaping **upward (decreasing board Y) from pads 22/23 into the
module footprint** and changing layers there to avoid X1 and XL1/XL2 below
the module. Check module underside clearance and land-pattern restrictions,
retain the inner ground planes, and stay outside the antenna keepout. This
is an alternative to the previously DRC-tested downward escape; the upward
route has not been validated or selected for you. Avoid running digital
edges alongside crystal traces. Keep the FDC trunk away from /SW and the
sensitive CIN inputs. Refill zones and complete DRC after routing.
