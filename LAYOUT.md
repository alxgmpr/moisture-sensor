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
| dielectric 1 | prepreg 7628 | **0.2104 mm** | 4.4 | RF reference gap |
| In1.Cu | copper | 0.0152 mm | — | **GND** (zoned — see §4) |
| dielectric 2 | core | 1.065 mm | 4.6 | |
| In2.Cu | copper | 0.0152 mm | — | power / **guard pour** |
| dielectric 3 | prepreg 7628 | 0.2104 mm | 4.4 | |
| B.Cu | copper | 0.035 mm | — | signal / guard |

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

**Use W = 0.38 mm.** FR4's ε_r falls with frequency — quoting 4.4 from a
datasheet measured at 1 MHz and designing a 2.4 GHz trace to it makes the trace
too narrow and the impedance high. The DRU allows 0.34–0.42 mm so you have room
to accept whatever the fab's own calculator returns.

**Confirm with the fab before ordering.** Prepreg thickness varies with copper
distribution and the pressed result is not exactly nominal. If impedance actually
matters to you, order with impedance control and let them adjust the width.

### RF routing rules (enforced in the DRU)

- **No vias in the RF path.** ANT → matching network → antenna all stays on F.Cu.
  A via adds series inductance, a stub, and a reference discontinuity.
- **0.5 mm clearance** to any non-RF net.
- **Unbroken In1.Cu ground directly beneath the entire RF run.** Any slot or
  split under the trace forces the return current around it and wrecks the
  impedance.
- **Stitching vias** along both sides of the RF trace. λ in FR4 ≈ 125/√ε_eff ≈
  69 mm at 2.4 GHz, so λ/20 ≈ 3.5 mm — **space stitching vias ≤ 3 mm.**
- Keep the run as short as physically possible. Put the matching network
  immediately at the ANT pin, not near the antenna.

### The two grounding rules that are easy to violate

From Nordic's reference (repeated here because they are invisible in a netlist):

1. **C6's ground connects ONLY to pin 32 (VSS_PA) on the top layer**, and pin 32
   connects to pin 49 (centre pad) *only underneath the package*.
2. **C9's ground connects only on the bottom ground layer.**

These are the same net electrically, which is why they are plain GND in the
schematic. If you want the DRC to police them, make them separate nets joined by
a net-tie footprint before you route.

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

**Recommendation: PCB inverted-F, copied from Nordic's reference layout.** Zero
cost, no placement risk, the matching network is already right, and the stake
form factor gives a natural ground-plane edge to work from.

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
| **Power** | GND, /VBAT, /VSYS, /VBUS_IN, /+3V3, /+3V3_MCU, /FDC_VDD, /SOLAR_* | 0.50 mm | 0.25 mm |
| Default | everything else | 0.20 mm | 0.20 mm |

`/VBAT`, `/VBUS_IN` and `/VSYS` additionally require **0.8 mm** minimum — they
carry the 500 mA charge current plus system load.

---

## 8. Component-specific keepouts

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

## 9. Open items

- Copy the IFA geometry and the ground-boundary position from Nordic's reference
  layout for the nRF54L15-QFAA. **[not yet downloaded]**
- Confirm 0.38 mm against the fab's impedance calculator for their actual
  pressed stackup.
- Electrode geometry: simulate or prototype for 10–30 pF dry with a swing inside
  ±15 pF.
- Decide net-tie vs documentation for the C6 / C9 grounding rules.
- Mechanical: antenna ≥ 50 mm above the soil line; vented enclosure section for
  the SHT45; sealed section for the electronics.
