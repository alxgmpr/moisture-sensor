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

**Use W = 0.38 mm.** The DRU allows 0.34–0.42 mm so you have room to accept
whatever the fab's own calculator returns.

### Checked against JLCPCB's parameters — 0.38 mm stands

The table above is a bare-microstrip Hammerstad solve. JLCPCB's calculator models
three things it does not, so it was worth re-running with their published numbers
(§1) rather than assuming they cancel:

| At W = 0.38 mm, h = 0.21040 mm, t = 0.035 mm | Z₀ |
|---|---|
| ε_r 4.2 (the assumption above), bare | 49.9 Ω |
| **ε_r 4.4 (JLCPCB's published 7628 value), bare** | **48.8 Ω** |
| ε_r 4.4, plus solder mask (0.6 mil, ε_r 3.8) | 48.2 Ω |
| ε_r 4.4, using the etch-tapered mean width (0.371 mm) | 49.5 Ω |

The two corrections push opposite ways and largely cancel: mask lowers Z₀ by
~0.6 Ω, the etch taper raises it by ~0.7 Ω. **0.38 mm lands at roughly 48.5–49.5 Ω
on JLCPCB's own material.** That is Γ = 0.012, VSWR 1.03 — about 0.01 dB of
mismatch loss, which is nothing next to an antenna whose matching network is an
unproven starting point (§3).

So the ε_r 4.2 choice was defensible but not actually necessary: at JLCPCB's
own 4.4 the exact 50 Ω width is 0.364 mm, and the difference between that and
0.38 mm is 1.2 Ω. Both sit inside the DRU's 0.34–0.42 mm window. **Do not respin
the trace for this.**

**Confirm with the fab before ordering.** Prepreg thickness varies with copper
distribution and the pressed result is not exactly nominal. If impedance actually
matters to you, order with impedance control and let them adjust the width — they
will solve it on the real pressed stackup with their own solver, which is a better
answer than any of the numbers above.

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

## 3. Antenna: PCB inverted-F vs chip

### The argument that actually decides it

**The matching network already in the schematic is Nordic's, and it is matched to
Nordic's reference antenna.** L2 2.7 nH, C6 1.5 pF, L3 3.5 nH, C9 2.0 pF,
L4 3.5 nH, C11 0.3 pF, C13 3.9 pF are only meaningful with that geometry.

- Take **Nordic's reference PCB antenna** → those values are a valid starting
  point and you tune from a known-good position.
- Take a **chip antenna** → discard all of them, start from the chip vendor's
  reference network, and retune from scratch.

That asymmetry is worth more than the small differences in the table below.

| | PCB inverted-F | Chip antenna |
|---|---|---|
| BOM cost | **zero** | ~$0.30 + a placement |
| Keepout needed | ~15 × 7 mm | ~10 × 5 mm |
| Typical efficiency, good ground | 50–70 % | 40–60 % |
| Part-to-part spread | excellent (etch-defined) | placement tolerance matters |
| Matching values in schematic | **valid** | must be replaced |
| Detuning near soil/water | high | high — no real advantage |

**Recommendation: PCB inverted-F.** Zero cost, no placement risk, and the stake
form factor gives a natural ground-plane edge to work from.

### The reference layout does not contain an antenna

The plan above said "copied from Nordic's reference layout". That is not
possible, and the reason is worth recording so it is not assumed again.

`nrf54l15-qfaa-reference-layout-0_8.zip` (and the QGAA 1.0 equivalent) contains
a **15 × 13 mm board with no PCB antenna**. The RF chain runs
`ANT → L2 → C6 → L3 → C9 → L4 → C11` and terminates at a pad on the board edge —
a coax or connector launch. It is an MCU support reference, not an antenna
reference. What it does give, and what is copied:

- matching-network placement relative to pin 31
- the C6-to-pin-32 and C9-to-bottom-layer grounding topology (§2 above)
- MCU support component placement

**Consequence for the matching network.** The argument in the table above — that
Nordic's L2/C6/L3/C9/L4/C11 values are "valid" because they match Nordic's
antenna — does not hold. There is no Nordic antenna. Treat those values as a
sensible starting point for a 2.4 GHz IFA, not as a known-good position, and
budget the VNA session accordingly.

### The IFA as drawn

Designed for this board's ground plane, in `lib/footprints.pretty/IFA_2450MHz.kicad_mod`,
placed by `tools_gen_pcb.py`. All dimensions are named constants — trim and re-run.

| | |
|---|---|
| Ground plane edge | board y = 11.5 mm, full width |
| Radiating arm | 18.5 × 1.0 mm at y = 2.5–3.5 |
| Shorting stub | 1.0 mm wide at x = 12.8, y = 2.5 → 11.5 |
| Feed stub | 0.5 mm wide at x = 16.8, y = 3.5 → 11.5 |
| Feed-to-short spacing | 4.0 mm — this is the impedance knob |
| Electrical length, short → open | ≈ 27.5 mm |

λ/4 is 31.2 mm in air and roughly 24–25 mm with FR4 loading on one side, so 27.5 mm
starts deliberately long: you can trim etched copper, you cannot add it.

The feed sits at x = 16.8 so the 50 Ω line runs straight up from U1 pin 31 after
the package is rotated 90°. No bend, no via.

**The antenna is a net tie.** An IFA is a shorted stub, so the feed is DC-grounded
through the shorting stub. The footprint declares `net_tie_pad_groups "1, 2, 3"`
— pad 1 on `/ANT_FEED`, pads 2 and 3 on `GND` — which is what stops DRC calling
it a short. Because the arm and stub sit on `GND` rather than the RF net class,
the DRU keepout exemption has to be written against the footprint reference
(`!A.memberOfFootprint('AE1')`), not against the net class.

**Switch to a chip antenna only if** the mechanical design cannot give you the
keepout. The commonly-cited reason — "a chip antenna coexists better with nearby
dielectric" — does not hold up here; both detune badly near wet soil, and the
mitigation is distance, not part choice.

### Soil proximity is the dominant effect, and it is mechanical

Wet soil has ε_r of roughly 20–30 with real conductivity. Anything in the
antenna's near field is going to load it. This is not fixable in the matching
network, only in the mechanical design:

- Put the antenna at the **top of the stake**, as far above the soil line as the
  enclosure allows. λ = 125 mm in air, so **aim for ≥ 50 mm of separation**
  (~0.4 λ) between the antenna and the soil surface.
- Nothing conductive above or beside the antenna: no battery, no copper pour, no
  screws, no metal-loaded plastic.

**Tune with the enclosure fitted and a realistic soil load in place.** A network
tuned on the bench in free space will be wrong once the board is in a pot. Budget
a VNA session with a pot of damp soil as part of bring-up.

Link budget is forgiving here — the BLE proxy is indoors and already deployed —
so losing several dB of efficiency to soil loading is survivable. Do not
over-engineer this at the expense of the measurement path.

### Keepout

Draw a rule area on **User.1 (AntennaKeepout)** covering the antenna and its
clearance. The DRU forbids tracks, vias, zones and pads inside it.

- The keepout must be **copper-free on all four layers**, ground pour included.
  A ground plane under an IFA shorts out its near field and destroys efficiency.
- Extend it to the board edge; do not ring the antenna with a ground guard.

---

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
| A antenna | 0 – 11.5 | no copper on any layer except AE1 |
| B electronics | 11.5 – 74.0 | 34.0 × 62.5 mm, solid In1.Cu |
| C probe | 74.0 – 155.0 | 20 mm wide, no ground on any layer |

Soil line at y = 115, so the antenna sits **112 mm above it** against the 50 mm
target in §3. Insert depth 40 mm. SENSE2 (air reference) at y 82–112 and SENSE1
(soil) at y 119–149 are both 16 × 30 mm — identical geometry is what makes the
ratiometric measurement in §5 cancel anything.

The probe leaves through a slot in the box end wall. R2.0 fillets at the shoulder
keep the stress off the inside corners.

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
- Window-pane the paste apertures on `QFN48_6X6_NOR` and `QFN32_5X5_NOR`. Both
  have a single full-area aperture on the thermal land (22.1 mm² and 13.0 mm²)
  and both lands are drawn at D2 *max* rather than nominal.
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
