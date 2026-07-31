# Layout & RF Constraints

Companion to [HARDWARE.md](HARDWARE.md). Everything here is encoded where it can
be: stackup in `moisture-sensor-carrier.kicad_pcb`, rules in
`moisture-sensor-carrier.kicad_dru`, net classes in the project file.

---

## 1. Stackup

4-layer is not optional here. Three separate requirements force it: a controlled
reference plane under the RF trace, a guard structure for the capacitive front
end, and a solid ground for the MCU. On 2-layer 1.6 mm FR4 a 50 Ω microstrip
would be ~2.9 mm wide, which settles it.

**JLC04161H-7628 equivalent, 1.6 mm:**

| Layer | Material | Thickness | ε_r | Role |
|---|---|---|---|---|
| F.Cu | copper | 0.035 mm | — | RF, signal, sense electrodes |
| dielectric 1 | prepreg 7628×1 | **0.21040 mm** | 4.4 | RF reference gap |
| In1.Cu | copper | 0.0152 mm | — | **GND** (zoned — see §4) |
| dielectric 2 | core | **1.065 mm** | 4.6 | |
| In2.Cu | copper | 0.0152 mm | — | power / **guard pour** |
| dielectric 3 | prepreg 7628×1 | 0.21040 mm | 4.4 | |
| B.Cu | copper | 0.035 mm | — | signal / guard |

### Order JLC04161H-7628 — plain, no suffix

**Corrected.** This section previously said 7628**D** was the only 4-layer 7628
variant with a single 7628 prepreg between the top layer and L2, and that the
core was 1.265 mm. Re-read against JLCPCB's own published stackup list
(*Controlled Impedance PCB Layer Stackup*, filtered to 1.6 mm / 1 oz outer /
0.5 oz inner) — **three** of the eighteen 4-layer entries have that single
0.21040 mm prepreg, not one:

| JLC stackup | Top → L2 | Core | Layers sum | |
|---|---|---|---|---|
| "No requirement Stackup" (the default) | **0.21040 mm** | 1.065 mm | **1.586 mm** | JLC calls this lowest cost, quickest turnaround |
| **JLC04161H-7628** | **0.21040 mm** | 1.065 mm | **1.586 mm** | **order this** |
| JLC04161H-7628D | **0.21040 mm** | **1.265 mm** | **1.786 mm** | same impedance, but 0.19 mm too thick |
| JLC04161H-7628E | 0.218 + 0.21040 = 0.428 mm | 0.6 | | no |
| JLC04161H-7628B | 0.218 + 0.218 + 0.1164 = 0.552 mm | 0.4 | | no |
| JLC04161H-7628C | 0.218 + 0.218 + 0.21040 = 0.646 mm | 0.15 | | no |
| JLC04161H-7628F | 0.218 + 0.218 + 0.21040 = 0.646 mm | 0.25 | | no |

Two things follow.

**The impedance argument is unchanged and still decides the order.** At
h = 0.428 mm a 0.38 mm trace is roughly 75 Ω, not 50, so B/C/E/F are still out.
Specify the stackup at order time and confirm it on the acknowledgement.

**But 7628D was the wrong pick, and that is what the total-thickness question in
NEXT-STEPS.md was detecting.** 7628D's layers sum to 1.786 mm because its core is
1.265 mm; plain 7628 sums to 1.586 mm, which is a real 1.6 mm board. Since both
have the identical 0.21040 mm top dielectric they give identical impedance, so
plain 7628 is strictly better — right thickness, and it is the cheaper/faster
default. The 1.265 mm core belonged to 7628D and has been reverted here and in
§5; the board file's 1.065 mm was right all along.

### JLCPCB's own material parameters

From page 1 of the same document. These matter because the §2 calculation below
was done with none of them:

| | |
|---|---|
| Prepreg 7628 ε_r | **4.4** (3313 → 4.1, 1080 → 3.91, 2116 → 4.16) |
| Core ε_r | 4.6 |
| Solder mask ε_r | 3.8 |
| Mask above trace / above substrate | 0.6 mil (0.01524 mm) / 1.2 mil |
| Etch taper | **trace top width = base width − 0.7 mil** (0.01778 mm) |
| Outer copper 1 oz | 0.035 mm |
| Inner copper 0.5 oz | 0.0152 mm |

The thin 0.21 mm top dielectric is what makes a sane-width 50 Ω microstrip
possible, and it is why the RF trace must reference **In1.Cu**, not B.Cu.

---

## 2. RF impedance — 50 Ω microstrip

Microstrip on F.Cu over In1.Cu, h = 0.2104 mm, t = 0.035 mm.

Thickness correction (Hammerstad):

```
ΔW = (t/π)(1 + ln(2h/t)) = (0.035/π)(1 + ln(12.02)) = 0.0388 mm
W_eff = W + ΔW
```

Solving `Z₀ = 120π / (√ε_eff · [W/h + 1.393 + 0.667·ln(W/h + 1.444)])`:

| ε_r | W_eff/h | W_eff | **W** |
|---|---|---|---|
| 4.4 (datasheet, ~1 MHz) | 1.92 | 0.404 mm | 0.365 mm |
| **4.2 (realistic at 2.4 GHz)** | **2.00** | **0.421 mm** | **0.382 mm** |

The table above is a bare-microstrip Hammerstad solve, and it is **not** what the
board uses. See below.

### W = 0.36 mm, from JLCPCB's own calculator

This is the number to trust, because it is the fab's solver on the exact stackup
being ordered rather than anything derived here. Run at
<https://jlcpcb.com/pcb-impedance-calculator> with 4 layers, 1.6 mm, 1 oz outer,
0.5 oz inner, 50 Ω **Single Ended (Non coplanar)**, signal layer **L1**, top ref
none, bottom ref **L2**:

| Stackup | Top → L2 dielectric | Trace width for 50 Ω | Finished thickness |
|---|---|---|---|
| **JLC04161H-7628** | 7628 RC 49% 8.6 mil → **0.2104 mm** | **14.12 mil = 0.3586 mm** | **1.59 mm**, *Standard* |
| JLC04161H-7628D | identical, 0.2104 mm | 14.12 mil = 0.3586 mm | 1.79 mm, *Special* |
| JLC04161H-3313A | 3313 ×2 → 0.1070 + 0.0994 = 0.2064 mm | 13.57 mil = 0.3447 mm | 1.58 mm, *Special* |

**The board now uses 0.36 mm.** The DRU's `opt` is 0.36 with the 0.34–0.42 mm
window kept, so there is still room to accept whatever the fab returns after
pressing.

Three things fall out of this, and none of them were visible from the hand calc:

**The calculator independently confirms §1.** It labels plain `JLC04161H-7628`
**Standard** at a finished 1.59 mm and every other 4-layer variant *Special* —
7628D comes back at **1.79 mm**, which is the thickness discrepancy that had been
sitting open in NEXT-STEPS.md. 7628 and 7628D return the *same* trace width, since
the top dielectric is identical; the only difference is board thickness and cost.

**0.38 mm was not 50 Ω.** Our Hammerstad model at JLCPCB's published ε_r 4.4
returns 50.39 Ω at their 0.3586 mm width — agreement to 0.4 Ω, which validates the
model — and the same model puts the old 0.38 mm at **48.8 Ω** (Γ = 0.012,
VSWR 1.024, return loss 38.5 dB). That is a small error and would not have broken
anything, but there is no reason to carry it when the fab's own answer is free.
The earlier ε_r 4.2 "realistic at 2.4 GHz" adjustment was what pushed the width up
to 0.38; JLCPCB solve at 4.4 flat.

**A 3313 stackup is marginally better and was not considered.** The calculator's
first suggestion is `JLC04161H-3313A`, which reaches 0.2064 mm using two thin
3313 prepregs. It is not being taken — 7628 is the *Standard* option, §1's whole
argument is built on it, and the difference is 0.004 mm of dielectric — but it is
worth knowing that "single 7628 prepreg" was a sufficient condition for a thin top
dielectric, never a necessary one.

**Still order with impedance control.** Pressed prepreg thickness varies with
copper distribution, and the ±10% on finished thickness above is real. Impedance
control lets them re-solve on the actual pressed stackup.

### RF routing rules (enforced in the DRU)

- **No vias in the RF path.** ANT → matching network → antenna all stays on F.Cu.
  A via adds series inductance, a stub, and a reference discontinuity.
- **0.5 mm clearance** to any non-RF net.
- **Unbroken In1.Cu ground directly beneath the entire RF run.** Any slot or
  split under the trace forces the return current around it and wrecks the
  impedance.
- **No stitching vias along the RF trace — corrected.** This previously said to
  space them ≤ 3 mm (λ/20; λ in FR4 ≈ 125/√ε_eff ≈ 69 mm at 2.4 GHz). That is a
  *coplanar waveguide* rule: it exists to tie top-side ground beside the trace
  down to the reference plane. This board is not CPWG. Zone B has exactly one
  ground layer, In1.Cu — F.Cu carries no ground pour beside the trace and neither
  does B.Cu — so a stitching via has nothing to stitch to. Four were placed during
  routing and KiCad reported all four as `via_dangling`, connected on one layer
  only. It is also self-consistent: W = 0.38 mm in §2 comes from the **microstrip**
  equation, and for microstrip the return current flows in the plane directly
  under the trace. Going CPWG instead would need F.Cu ground either side at a
  controlled gap and would make 0.38 mm the wrong width.
- Keep the run as short as physically possible. Put the matching network
  immediately at the ANT pin, not near the antenna.

### The two grounding rules that are easy to violate

From Nordic's reference:

1. **C6's ground connects ONLY to pin 32 (VSS_PA) on the top layer**, and pin 32
   connects to pin 49 (centre pad) *only underneath the package*.
2. **C9's ground connects only on the bottom ground layer.**

These are the same node electrically, so they are invisible in a netlist. They
are now split into their own nets and rejoined by net ties, so the DRC polices
them instead of a comment in a markdown file:

| Net | Nodes | Tie | Placement |
|---|---|---|---|
| `/GND_PA` | C6.2, U1.32 | **NT1** → GND | under the U1 centre pad, F.Cu |
| `/GND_C9` | C9.2 | **NT2** → GND | B.Cu |
| `/GND_PVSS2` | C24.2, U2.6 | **NT3** → GND | at the via to the ground layer |

The third one is the nPM1300's, found in Nordic's own reference schematic
(datasheet §9.3.2), which annotates PVSS1 **"Net tie"** and **"Via to GND-layer
on PVSS1"**. Pin 6 is *BUCK2 power ground*, not a general ground pin — it should
reach the plane at one controlled point rather than merging into the top-layer
pour. C24 returns to it too, so the high-di/dt loop SW2 → L10 → C24 → PVSS2
closes locally instead of through the plane. PVSS1 (pin 2) stays on plain GND
because BUCK1 is disabled and carries nothing.

Both ties are `Device:NetTie_2` / `NetTie:NetTie-2_SMD_Pad0.5mm`. Three DRU rules
enforce the routing half:

- `C6 ground takes no vias` — a via anywhere on `/GND_PA` defeats rule 1
- `C6 ground stays on the top layer`
- `C9 ground never touches an inner plane` — a short stub from C9's pad down to a
  via is unavoidable; reaching In1.Cu or In2.Cu is not
- `BUCK2 power ground is short and fat` — 0.5 mm minimum on `/GND_PVSS2`, the
  same as the switch node whose return it carries

The placement half — NT1 under U1, NT2 on B.Cu — is asserted in
`tools_gen_pcb.py`, because DRC has no way to express it.

`/GND_PA` also carries a PWR_FLAG. U1 pin 32 is a power *input*, and splitting it
off GND left it with only passive pins to drive it.

---

## 3. Antenna: U.FL connector + external adhesive antenna

**The PCB inverted-F is gone.** AE1 has been replaced by **J5, a Hirose
U.FL-R-SMT-1(10) receptacle**, feeding an adhesive antenna mounted inside the
enclosure on a U.FL pigtail. Two things drove it, and the second one is the
bigger deal.

**It was the only way the board fits the box.** The 1551WK has four internal
corner bosses that need PCB corner reliefs (§9), and at the antenna end those
reliefs cut straight through the IFA's radiating arm.

**It makes Nordic's matching network correct rather than a guess.** This section
used to carry a long caveat: the QFAA reference layout contains *no PCB antenna*,
so L2/C6/L3/C9/L4/C11 were "a sensible starting point for a 2.4 GHz IFA, not a
known-good position". What the reference *does* contain is the chain
`ANT → L2 → C6 → L3 → C9 → L4 → C11` terminating at a board-edge pad **for a coax
or connector launch**. That is exactly what a U.FL is. The values are now being
used in the configuration Nordic characterised them in, and the caveat is
withdrawn.

### J5 — Hirose U.FL-R-SMT-1(10)

Verified against the Hirose U.FL catalogue drawing:

| | |
|---|---|
| Impedance / bandwidth | **50 Ω, DC–8 GHz** |
| V.S.W.R. | ≤1.3 to 3 GHz, ≤1.4–1.5 to 6 GHz (plug dependent) |
| Mated height | 1.9–2.4 mm nominal, 2.0–2.5 mm max |
| Durability | **30 mating cycles** — mate once in service |
| Land pattern | 4.00 mm GND span, SIG at 1.9 mm, GND pads 2.2 × 1.0 mm |
| Note on the drawing | **"No conductive traces in this area"** between the pads |

KiCad's `Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical` matches: its GND
pads are 1.05 mm rather than 1.00 mm tall, but on ±1.475 mm centres, which gives
Hirose's specified 4.00 mm outer span. Inside the ±0.05 mm tolerance either way.

Placed at board **(16.8, 12.0)**, rotated 90° so the signal pad faces the
matching network. **The RF run from U1 pin 31 to the signal pad is 6.554 mm**,
against λ/8 = 8.6 mm — 76 % of the limit, where the PCB antenna sat at 99.8 %.

### What this changed elsewhere

- **Zone A is now ordinary board.** ZoneB_GND floods it. The `AntennaKeepout` and
  `AntennaCrossing` rule areas and the DRU rule that policed them are deleted.
- **Soil proximity stops being a PCB problem.** It becomes a question of where you
  stick the antenna in the box — still aim for as much separation from the soil
  line as the enclosure allows, but no copper geometry depends on it.
- **The VNA session becomes a check, not a tuning exercise.** Still worth doing
  with the enclosure closed and a realistic soil load, because the adhesive
  antenna and its position inside a plastic box are now the unknowns.

## 4. Ground plane strategy — the board is zoned, not uniformly poured

The instinct to flood every layer with ground is wrong on this board. It breaks
both the antenna and the moisture measurement. Think of the stake as three zones
along its length:

```
┌──────────────────────────┐
│  ZONE A - ANTENNA        │  no copper on any layer
│  (top of stake)          │  In1.Cu ground STOPS at this boundary
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

**Zone A**: ground stops cleanly at the boundary. That boundary edge is the
IFA's ground reference — its position is part of the antenna design, so copy it
from the reference layout rather than choosing it.

**Zone B**: solid unbroken In1.Cu. No splits under the RF trace or the MCU.
Stitch generously.

**Zone C**: no ground, and the reason is quantitative — see §5.

---

## 5. Capacitive front end

### Why Zone C has no ground plane — the numbers

The FDC1004's shield driver is rated **400 pF maximum** (SNOSCY5, DRV). The
guard pour's capacitance to any nearby ground is what loads it.

Parallel-plate estimate, `C/A = ε₀ε_r/d`:

| Guard placement | d | C per area | Area to hit 400 pF |
|---|---|---|---|
| F.Cu guard over In1.Cu ground | 0.2104 mm | 1.85 × 10⁻⁷ F/m² | **21.6 cm²** |
| In2.Cu guard over In1.Cu ground | 1.065 mm | 3.82 × 10⁻⁸ F/m² | 105 cm² |

A probe 2 cm wide by 10 cm long is 20 cm² of guard — **right at the limit** if
there is ground plane under it. Delete the ground from Zone C and the guard's
capacitance collapses to edge fringing, which is negligible.

Ground near a *sense* trace is worse still: it is measured capacitance, so it
directly consumes CAPDAC range and couples in noise. The DRU enforces 1 mm
minimum sense-to-Power clearance for this reason.

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

- **SHLD1 and SHLD2 are internally shorted** (SNOSCY5 §7.2.2), so tying them
  together in the schematic is correct, not a shortcut.
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

Two aggressors: **nPM1300 SW2** (3.6 MHz in PWM) and the **nRF54L15 DCC** node.
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

- Put the PMIC and the MCU's DC/DC at the **bottom** of Zone B, the RF at the
  **top**, and the FDC1004 near the Zone C boundary but shielded from both.
- Keep both switching loops physically tiny: SW2 → L10 → C24 and DCC → L1 → C3
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
| **RF** | /ANT, /ANT_FEED, /RF_A, /RF_B, /RF_C | 0.38 mm | 0.30 mm |
| **SENSE** | /SENSE1, /SENSE2 | 0.25 mm | 0.50 mm |
| **SHIELD** | /SHLD | 0.30 mm | 0.20 mm |
| **SWITCH** | /SW2, /DCC | 0.50 mm | 0.30 mm |
| **Power** | GND, /GND_PA, /GND_C9, /VBAT, /VSYS, /VBUS_IN, /+3V3, /FDC_VDD, /SOLAR_* | 0.50 mm | 0.25 mm |
| Default | everything else | 0.20 mm | 0.20 mm |

`/VBAT`, `/VBUS_IN` and `/VSYS` additionally require **0.8 mm** minimum — they
carry the 500 mA charge current plus system load.

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
each side and the wall runs 34.46 → 37.00. `tools_gen_pcb.py` asserts U4 starts
beyond 37.00 — otherwise the sensor sits *in* the wall rather than outside it.

**Enclosure modification required.** A milled slot in the long side wall,
**5.0 mm wide × board thickness**, centred at y = 20.6 from the board's top
edge, at **4.00–5.60 mm above the box floor** (the board sits on the 4.00 mm
posts). Hammond do factory milling. This is a second opening on top of the probe
slot, and it is not sealed — pot it or accept the loss of IP rating there.

The tab keeps a `SHT45_Jut` rule area that bans pour, so it carries only the
four traces and no ground fill. The die keepout from datasheet §5.3 stays as it
was. The tab is clear of the cell, and the ground pour stops at x = 33.7 so no
plane copper reaches it.

**SHT45 — no copper underneath.****SHT45 — no copper underneath.** Datasheet §5.3: *"Soldering of the central die
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

Drawn by `tools_gen_pcb.py`. Edit that and re-run; do not hand-edit the
`.kicad_pcb`. It self-checks and aborts rather than emitting broken geometry.

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
| A antenna | 0 – 11.5 | **now ordinary board** — J5 U.FL + ground pour |
| B electronics | 11.5 – 74.0 | 34.0 × 62.5 mm, solid In1.Cu |
| C probe | 74.0 – 155.0 | 20 mm wide, no ground on any layer |

Soil line at y = 115, so the antenna sits **112 mm above it** against the 50 mm
target in §3. Insert depth 40 mm. SENSE2 (air reference) at y 82–112 and SENSE1
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

### Height budget — the thing that bit

Board on the 4.00 mm posts: 4.00 + 1.6 (PCB) leaves **11.70 mm** to the lid.
A 5 mm cell taped to the inside of the lid leaves **6.70 mm** of clear component
height under it, and 11.70 mm in the two ~12 mm end bands the cell does not cover.

This is why the cell is a 503450 (5 mm, ~1000 mAh) and not the 103450 (10 mm,
2000 mAh). The runtime penalty is small because self-discharge scales with
capacity: `runtime = 0.95·C / (0.24·C + 42.8)` in mAh/yr, from HARDWARE.md §7,
which gives 3.63 yr at 2000 mAh and 3.36 yr at 1000 mAh — a 7 % cost for 5 mm.
The same formula has an asymptote at 3.96 yr, so no cell that fits this box gets
meaningfully past 3.6 years anyway.

**Mounting screws.** The two antenna-end holes are 6 mm from the radiating arm.
Use **nylon** #2 screws in those two positions; steel there will detune the
antenna and no amount of matching fixes it.

### Placement

All 56 components placed by `tools_gen_pcb.py`, 528 mm² of courtyard in 2125 mm²
of Zone B (25 %). The script asserts, and aborts on failure: courtyard overlap,
edge clearance, mounting-screw clearance, nothing but AE1 in Zone A, the two
net-tie placement rules, and SENSE-to-SWITCH separation.

| Band | y | Contents |
|---|---|---|
| RF | 12.5–19.3 | L2/C6/L3/C9/L4/C11 in a column at x = 16.8 |
| MCU | 19.4–31 | U1 (rot 90), X2 top-left, X1 below, DECD/DECA/DCC cluster left |
| Debug / ambient | 33–39 | J4 Tag-Connect, U4 + C27 right, I²C pull-ups |
| Power in | 40–52 | J1 USB-C left edge, J3 + D5 right, solar reserve |
| PMIC | 51–62 | U2, SW2 → L10 → C24 loop, bulk caps |
| Sense / battery | 63–73 | U3 hard against the Zone C boundary, TP1–TP3, J2, LEDs |

**U1 is rotated 90°.** Its original right edge goes to the top, which puts pin 31
(ANT) pointing straight at Zone A, X2 near pins 34/35, X1 below near pins 1/2,
and DECD/DECA/DCC on the left. The RF run from pin 31 to the ground boundary is
about 8.2 mm — λ/8 at 2.4 GHz in FR4 is 8.6 mm, so this is at the limit and
wants stitching at the full ≤3 mm density.

**J1 overhangs the left board edge.** The HRO footprint mates toward +Y, so it is
rotated 270° with its origin at x = 3.5, putting the body face 0.2 mm proud of
the edge. Its courtyard legitimately leaves the board; the script checks its
*pads* are on copper instead, and moves its silk to F.Fab so the router does not
clip it.

**Probe electrodes** are filled zones on F.Cu — SENSE1 and SENSE2, each
16 × 30 mm — with the SHLD guard pouring around them at 0.2 mm and guard on
In2.Cu and B.Cu beneath. Guard-to-ground overlap is only the 33 mm² where the
F.Cu guard crosses the Zone B boundary, about 6 pF against the 400 pF shield
limit.

**LAYOUT.md §6 caveat.** "PMIC and the MCU's DC/DC at the bottom" is only half
achievable. The nRF's DC/DC is at pin 46 and has to stay tight to U1 at the top;
pins 31 and 46 are two package edges apart and nothing moves them. What did move
to the bottom is the nPM1300 SW2 loop, which is the 3.6 MHz aggressor the 3 mm
SENSE-to-SWITCH rule is written for. U3 ends up 7.6 mm from U2 and 12.2 mm from
L10.

## 10. Open items

- **USB-C breaks IP68.** A port cutout in a watertight box needs a sealed cover,
  or J1 becomes a service-only connector reached by opening the lid.
- **SHT45 in a sealed box measures the box, not the room.** Temperature still
  works; RH does not. Needs a PTFE membrane vent in the lid over U4 — the
  sensor's own `-AD1F` membrane protects the die but does not help if the
  enclosure is sealed.
- Confirm the 1551WK corner-relief geometry and the Ø2.6 hole pattern against
  Hammond's STEP model before fab. The drawing's `62.00 × 22.00` and `R4.42` are
  ambiguous at the resolution published; `55.00 × 25.00` is unambiguous and is
  what is drawn.
- Confirm 0.38 mm against JLCPCB's own impedance calculator for the **7628D**
  pressed stackup. The nominal dielectric is confirmed at 0.21040 mm, but the
  pressed result varies with copper distribution — order with impedance control
  and let them adjust the width if it matters to you.

### Confirmed against Nordic's nPM1300 EK (PCA10152)

Plane-level read of the EK layout, not a coordinate-level copy — it is a large
multi-function dev board and its PMIC loop geometry is not directly
transferable. What it confirms:

- **solid, unbroken inner ground plane** under the PMIC, with dense via
  stitching throughout and a visibly higher via density around the regulator
- a **separate inner power plane** carved into regions by routed splits
- SW2 → inductor → 10 µF output cap, the same topology as our SW2 → L10 → C24

That is the Zone B plan in §4 already: solid In1.Cu, stitch generously, In2.Cu
as the power/guard layer. No change follows from it.

### Confirmed against TI's FDC1004EVM (SV601093B)

TI's own evaluation board builds the sense front end exactly the way §5
specifies, which is worth recording as independent confirmation rather than a
change:

- the sense electrode is a **solid filled area on the top layer**
- the **guard is a solid plane directly beneath it on the opposite layer**
- guard copper also **rings the electrode on its own layer** across a narrow gap

That is the Zone C construction as drawn — F.Cu electrodes, SHLD guard pouring
around them at 0.2 mm, guard on In2.Cu and B.Cu beneath.
- **X2 land pattern.** Epson's recommended FA-128 footprint is four pads on a
  roughly 1.45 × 1.15 mm envelope; KiCad's generic `Crystal_SMD_2016-4Pin` uses
  0.9 × 0.8 mm pads on ±0.7 / ±0.55 centres, a 2.3 mm outer span. Build an
  Epson-specific footprint, as was needed for X1.
- **Confirm C0 for the FA-128 with Epson.** The datasheet does not publish it,
  and it is half of what Figure 17 checks.
- Electrode geometry: simulate or prototype for 10–30 pF dry with a swing inside
  ±15 pF.
- ~~Window-pane the QFN paste apertures~~ — **done.** Lands moved to D2 nominal
  (4.6 mm and 3.5 mm, from the vendor package drawings) with 3×3 aperture arrays
  at 66 % coverage. See NEXT-STEPS.md.
- Neither QFN footprint has centre-pad vias. Nordic's reference puts a grid
  under U1 pad 49; add them when routing. **Watch NT1** — the via grid must not
  bridge GND_PA to GND anywhere except at the tie.
- **Routing.** 128 unconnected items and 4 isolated-copper warnings, all of them
  "nothing is routed yet". The isolated fills are the two sense electrodes and
  the Zone C guard, which connect once U3's pins are routed into the probe.

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
- **Both Nordic QFN footprints carry their pin-1 `*` marker twice**, at identical
  coordinates on identical layers, once in the old unquoted-layer block and again
  in the converted one. It prints on top of itself and DRC reports a silkscreen
  overlap every run. `tools_gen_pcb.py` strips the duplicates at load time rather
  than editing the vendor files.
