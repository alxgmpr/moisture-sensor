# Indoor Capacitive Soil Moisture Sensor — Hardware Design

nRF54L15-QFAA · nPM1300 (QFN32) · FDC1004 · BTHome v2 over BLE

All values below are cited from the source that was checked. Anything marked
**[assumed]** has not been verified and needs your sign-off.

**Revision note.** This document originally specified a BQ25185 linear charger
plus a TPS7A02 LDO. That was replaced by the nPM1300 PMIC — rationale and the
numbers behind the decision are in §9.

---

## 1. Power tree

```
USB-C VBUS ─────────────────────────────┐
                                        ├──► nPM1300 VBUS ──► VSYS ──► BUCK2 / VOUT2 3.3 V ─┬─► nRF54L15
Solar ──► 5 V pre-reg ──► D5 (Schottky) ┘         │                                         ├─► I2C pullups (always on)
                                                  │                                         └─► LOADSW1 ──► FDC1004
                                                  └──► VBAT ──► Adafruit 258 Li-ion 1200 mAh
```

USB-C VBUS feeds nPM1300 VBUS directly. The solar branch carries the only diode —
D5 blocks solar from back-feeding VBUS, and USB cannot back-feed the panel. One
diode, on the branch that can afford the drop.

**The 3.3 V rail must come from BUCK2, not BUCK1.** This is not a preference. The
VSET resistor tables are asymmetric:

- **Table 17 (R_VSET1 → VOUT1)** tops out at **2.7 V** (250–500 kΩ).
- **Table 18 (R_VSET2 → VOUT2)** reaches **3.3 V** at 250–500 kΩ.

TWI *can* reprogram either buck up to 3.3 V after boot, but the VSET pins define
the **start-up** voltage, and this design cold-boots from System OFF every hour.
Coming up at 2.7 V and then raising the rail would under-volt the FDC1004 on
every single wake. Use BUCK2 and be done with it.

**BUCK1 is disabled by grounding VSET1** (<100 Ω → 0 V / OFF, Table 17). Running
one buck instead of two saves 300 nA (800 nA vs 1100 nA, Table 3). Note the
datasheet warning: *do not leave VSET[n] floating* — a hard ground is the correct
way to disable BUCK1, not a no-connect.

Also from §6.3: **the outputs of BUCK1 and BUCK2 must never be tied together.**

**Never *leave* a buck in forced PWM mode.** Table 3: one BUCK in PWM at no load
is **4.0 mA** — 5000× the Auto-mode figure. In Auto mode the converter picks
hysteretic below I_HYSTTHRES = 40 mA and PWM above I_PWMTHRES = 90 mA. Every load
here is orders of magnitude below both, so it stays hysteretic permanently.
Forced PWM left on would destroy this power budget outright — verify
`BUCKnPWMSET` at bring-up.

That said, PWM should be forced **transiently** during each capacitance
measurement to cut supply ripple: see §5, where hysteretic ripple costs ~0.68 fF
of measurement error via the FDC1004's PSRR. Enter PWM, convert, return to Auto.
The cost is ~0.2 mAh/yr.

---

## 2. nRF54L15 support circuitry

From Nordic's **Circuit configuration 1 for QFN48 (QFAA)** — "DCDC: supplied by
battery or external supply", NFC disabled. Correct config: internal DC/DC on, no NFC.

Topology below is **Nordic's QFAA reference layout 0.8**, not a generic
decoupling scheme. The DC/DC output does *not* return to VDD — it goes
`DCC → L1 → DECD`, then `DECD → FB1 → DECA`, and **DECA and DECRF are the same
net**. VDD is fed straight from the 3.3 V rail with no ferrite in the supply path.

| Des | Value | Description | FP | Net / pin |
|---|---|---|---|---|
| U1 | nRF54L15-QFAA | SoC, QFN48 6×6 mm, 0.4 mm pitch | QFN-48 | — |
| L1 | 4.7 µH | **LQM18PN4R7MFRL**, 120 mA, ±20%, DCR 0.55 Ω max | 0603 | DCC (46) → DECD (45) |
| C1 | 2.2 µF | X6T, ±20%, 2.5 V | 0201 | DECD (45) → GND |
| FB1 | 120 Ω @ 100 MHz | Ferrite bead, 200 mA, 500 mΩ max | 0201 | DECD (45) → DECA (43) |
| C2 | 2.2 µF | X6T, ±20%, 2.5 V | 0201 | DECA → GND |
| C12 | 10 nF | X7R, 6.3 V | 0201 | DECA → GND |
| C5 | 2.2 nF | X7R, ±10%, 10 V | 0201 | DECA → GND |
| C3 | 10 µF | X6S, ±20%, 6.3 V | 0402 | VDD bulk |
| C4, C7, C8, C10 | 100 nF | X7R, ±10% | 0201 | one per VDD pin (10, 22, 36, 47, 48) |
| R1 | 1 kΩ | ±1%, 0.05 W | 0201 | RESET (30) → SWD header |
| C13 | 3.9 pF | C0G, ±0.25 pF, 50 V | 0201 | RESET (30) → GND |
| X1 | 32.768 kHz | **CM8V-T1A, C_L = 7 pF, ±20 ppm, drive ≤ 0.5 µW** | 2012 2-pin | XL1 (1) / XL2 (2) |
| X2 | 32 MHz | **FA-128, C_L = 8 pF, ±40 ppm total, drive ≤ 100 µW** | 2016 4-pad | XC1 (34) / XC2 (35) |

**Things that are easy to get wrong here**, all of which this document got wrong
before the reference layout was checked:

- **DECRF (33) is not separately decoupled.** It ties to DECA. A 100 nF of its
  own is not in Nordic's BOM.
- **FB1 is not in the VDD supply path.** It sits inside the DC/DC filter between
  DECD and DECA. Putting it in series with VDD is a different circuit.
- **C13 3.9 pF is the RESET filter, not an RF component.** It appears adjacent to
  the matching network on Nordic's sheet, which invites exactly that mistake.
- **C5 2.2 nF is on DECA**, not on RESET.

### Crystal load capacitance — your explicit question

**No discrete load caps on either crystal.** Nordic's reference BOM lists none on
XC1/XC2 or XL1/XL2, because both oscillators have internal trimmable banks:

- **HFXO:** internal caps **4.0 pF to 17.0 pF in 0.25 pF steps**
  (`XOSC32M.CONFIG.INTCAP`). X2's C_L = 8 pF is inside that range.
- **LFXO:** internal caps **3 pF to 18 pF in 0.65 pF steps** (`XOSC32KI.INTCAP`).
  X1's C_L = 7 pF is inside that range.

You specify the crystal's C_L in part selection and match it in firmware via the
INTCAP registers. The register value is **not** the capacitance directly — it is
computed from the desired C_L and per-device factory trim values in `FICR->
XOSC32MTRIM` / `XOSC32KTRIM`. Note the programmed value is the capacitance seen
across the crystal terminals **including pin capacitance but excluding PCB
stray**, so keep the XC1/XC2 and XL1/XL2 traces short and account for stray
separately. The matching happens in software, not in copper. Budget a
trim step at bring-up: measure the 32 MHz carrier and adjust INTCAP until the
frequency error is centred.

**Load capacitance is capped at 9 pF on both oscillators** (§11.9.1/11.9.2:
C_L 6 pF min, 9 pF max). Most 32.768 kHz crystals ship at 12.5 pF and are simply
not usable — filter on C_L before anything else. LFXO drive level is also capped
at **0.5 µW**, which is low. ESR is specified as a curve of max ESR against C0
for a given C_L (Figure 17), not a single number.

**ppm requirements.** BLE requires ±50 ppm on the active carrier; the datasheet
states the HFXO requirement as **±40 ppm** for BLE and ±60 ppm for 2.4 GHz
proprietary. LFXO for BLE is **±500 ppm**, so the ±20 ppm reference part is
heavily over-specified for our non-connectable advertising — it is just what the
reference BOM calls for. X2 at ±40 ppm
*total* (initial + temperature + ageing) leaves 10 ppm margin — tight by design;
do not substitute a ±50 ppm part. The LFXO's ±20 ppm is far tighter than needed:
because you advertise **non-connectable only**, there are no connection events, so
the usual ±500 ppm sleep-clock requirement doesn't bind. Even 250 ppm drifts the
hourly wake by 0.9 s. The LFXO exists to clock GRTC through System OFF; ±20 ppm is
over-specified for that, but it is the reference BOM part and the cost delta is nil.

### RF matching network

| Des | Value | Part |
|---|---|---|
| L2 | 2.7 nH | LQP03HQ2N7B02 |
| L3, L4 | 3.5 nH | LQP03HQ3N5B02 |
| C6 | 1.5 pF | GJM0335C1E1R5WB01 |
| C9 | 2.0 pF | GJM0335C1E2R0WB01 |
| C11 | 0.3 pF | C0G ±0.1 pF, 50 V, 0201 |

Chain: `ANT (31) → L2 → [C6↓] → L3 → [C9↓] → L4 → [C11↓] → antenna`. All three
shunts go to ground; there is no series element after C11. **C13 is not part of
this network** — see the RESET note above.

**Two grounding rules from Nordic, easy to violate and hard to debug:**

1. **C6 ground must connect ONLY to pin 32 (VSS_PA) on the top layer**, and pin 32
   must connect to pin 49 (centre pad) *only underneath the package*.
2. **C9 ground must be isolated from all ground layers except the bottom ground
   layer.**

Nordic notes the antenna filtering components are subject to change — re-check
against the current reference before ordering.

---

## 3. PMIC — nPM1300

**Package: QFN32 5×5 mm.** Not the WLCSP. §5.2 states all CSP variants are
sensitive to visible and near-IR light and must be shielded by encapsulation or
coating. For a sensor that may sit in a window, that is a failure mode you do not
need. QFN32 also has better thermals: R_θJA 24.2 °C/W vs 48.3 °C/W for CSP.

### Configuration

| Function | Setting | Notes |
|---|---|---|
| BUCK2 → VOUT2 | 3.3 V, **Auto mode**, R_VSET2 = 250–500 kΩ 1% | Powers nRF54L15 and feeds LSIN1 |
| BUCK1 | **Disabled**, VSET1 hard-grounded (<100 Ω) | Saves 300 nA. Do not float VSET1 |
| LOADSW1 | Switch mode, LSIN1 from **VOUT2**, gates FDC_VDD | Replaces the discrete PMOS |
| LOADSW2 | Unused | — |
| Charge current | 500 mA, I²C-set | Range 32–800 mA, adjustable at runtime |
| Termination voltage | 4.2 V | Range 3.5–4.45 V |
| VBUS input current limit | Set after USB detection | **Defaults to 100 mA on every reset** |
| NTC | 10 k NTC in pack | JEITA compliant |
| LED0 / LED1 | Charge status | 5 mA low-side drivers |

**LSIN1 must be fed from VOUT2 (3.3 V), not from VSYS.** LOADSW1 in switch mode
passes its input through unregulated. VSYS swings 3.0–4.5 V, which would put up to
4.5 V across the FDC1004 against its ~3.6 V maximum. Feeding the load switch from
the already-regulated 3.3 V rail keeps the FDC1004 in spec in every battery and
charging state.

**Never supply the application directly from VBAT.** §8.2 is explicit: doing so
*"can interrupt the battery charging process causing unwanted behavior from the
charger."* Use VOUT1, VOUT2, or VSYS. This design uses VOUT2 throughout.

**V_SYSMIN = 2.7 V** is the minimum VSYS at which a BUCK will enable. Below that
the 3.3 V rail does not come up at all — which is well under any sane battery
cutoff, but worth knowing when debugging a deeply discharged cell on the bench.

### Support components

Derived from Nordic's reference Configuration 1 (Figure 59, Table 39), reduced to
our single-buck case. Designators are ours.

| Des | Value | Description | FP | Net |
|---|---|---|---|---|
| U2 | nPM1300-QEAA | PMIC | QFN32 5×5 | — |
| C20 | 1.0 µF | X5R, 10 V, ±10% | 0603 | VBUS (21) |
| C21, C22 | 10 µF | X5R, 25 V, ±20% | 0603 | VSYS (20), PVDD (4) |
| C23 | 2.2 µF | X7R, 16 V, ±10% | 0603 | VBAT (19) |
| C24 | 10 µF | X5R, 25 V, ±20% | 0603 | VOUT2 (32) |
| C25 | 100 nF | X5R, ±10% | 0201 | VDDIO (12) |
| C26 | 1 µF | X7R, 10 V | 0402 | FDC_VDD (LSOUT1, 29) |
| L10 | 2.2 µH | **DCR ≤ 400 mΩ, I_sat > 350 mA, I_max > 200 mA, ±20%** | 0806 | SW2 (5) → VOUT2 |
| R20 | 250–500 kΩ 1% | R_VSET2, sets VOUT2 = 3.3 V | 0201 | VSET2 (16) |
| R21 | 0 Ω | Grounds VSET1, disables BUCK1 | 0201 | VSET1 (17) |
| R22, R23 | 4.7 kΩ | TWI pull-ups — **on FDC_VDD, see §5** | 0402 | SDA (13), SCL (14) |
| R24 | 10 kΩ NTC | Battery thermistor, β = 3435 | — | NTC (18) |

Inductor selection is not a free choice — Table 19 requires I_sat > 350 mA even
though our steady load is microamps, because the hysteretic-mode peak current is
set by the converter, not by the load. Do not substitute a physically smaller part
with a lower saturation rating.

Output capacitance must give **effective C ≥ 4 µF with ESR ≤ 50 mΩ** (Table 20).
A 10 µF X5R 0603 derates substantially at 3.3 V bias — check the manufacturer's
DC-bias curve rather than trusting the nameplate value.

C26 on FDC_VDD is deliberately **1 µF, not the 10 µF Nordic shows**. That rail is
power-cycled every hour, so a smaller cap settles faster; 1 µF is ample for the
FDC1004's sub-milliamp draw. The recharge cost either way is negligible (10 µF to
3.3 V × 8760 wakes ≈ 0.08 mAh/yr).

**Leave VBUSOUT (22) unconnected.** It exists so a host SoC with USB can sense
VBUS. The nRF54L15 has no USB peripheral, and VBUSOUT can sit near 5 V — well over
the nRF54L15's VDD + 0.3 V pin limit. Do not run it to a GPIO. Read VBUS presence
over TWI from the PMIC's own status registers instead. Nordic also warns VBUSOUT
*"is only for host sensing and should not be used as a source."*

**The input current limit resets to 100 mA.** §6.1.3: the default VBUS limit is
IBUS100MA and it reverts to that default on a reset *or* on a cable
unplug/replug. Host firmware must re-detect and re-configure the limit via
`VBUSINILIM0` + `TASK.UPDATE.ILIMSW` after every reset. If you forget, charging
silently runs at 100 mA and a full charge takes 20+ hours. This is the single
easiest way to get a "why is charging so slow" bug.

**CC1/CC2 need no external resistors.** §6.1.3: these pins have internal 5.1 kΩ
pull-downs (R_d, Table 9) and must connect *directly* to the USB-C connector for
detection to work. Do not add the usual discrete 5.1 k pair.

### Thermal at 500 mA

You chose 500 mA earlier. It carries over, and the nPM1300 handles it better than
the BQ25185 would have:

- R_θJA = **24.2 °C/W** (QFN32) versus 68.3 °C/W for the BQ25185's DLH. Nearly 3×
  better, so the same dissipation produces roughly a third of the temperature rise.
- Configurable thermal regulation, plus `DIETEMPSTOP` / `DIETEMPRESUME`
  host-programmable thresholds (§3.5) — you can stop and resume charging at
  temperatures you choose.
- Global thermal shutdown at **TSD = 120 °C**, hysteresis 20 °C.

Because charge current is I²C-settable, firmware can also simply reduce it when
the die ADC reads hot. That is a better answer than picking a resistor and hoping.

### Battery pack requirement — this changes your PCM position

§3.4 states that battery packs connected to VBAT **must** contain:

- Overvoltage protection
- Undervoltage protection
- Overcurrent discharge protection
- Thermal fuse, *if* an NTC thermistor is not present

Your brief said the 103450's PCM is "present but not trusted" and that the
charger's own undervoltage lockout was the real protection. Under the nPM1300
that position no longer holds — Nordic requires the pack protection as part of the
safety case. Either trust the PCM (and verify it) or fit an NTC so the thermal
fuse requirement is satisfied by JEITA monitoring. **Fit the NTC.** It costs one
part, it is what the JEITA feature is for, and it removes the argument.

### Battery pack — DW01P + 8205A, and it has no thermistor

Identified by inspection: **DW01P** protection IC, **8205A** dual N-MOSFET,
two resistors marked **101 (100 Ω)** and **201 (200 Ω)**, one capacitor, and
**no NTC**. That matches the standard DW01P application circuit — the 100 Ω plus
the capacitor form the RC filter on the IC's VDD, and the 200 Ω is the current-
sense series resistor.

**[DW01P figures below are typical for the part family and were not read from a
datasheet — get the DW01P datasheet to confirm.]**

| DW01P parameter | Typical | Consequence for this design |
|---|---|---|
| Over-discharge detect | **~2.4 V** | far below our functional floor — see below |
| Over-charge detect | **4.25 V ±0.05** | worst case trips at **4.20 V** — see below |
| Operating current | **~3 µA** | matches the 3 µA assumed in §7. Good |
| Over-current detect | 150 mV / R_DS(on) ≈ 3 A | 6× our 500 mA charge. No interaction |

**1. TH1 is now fitted, not DNP.** §3.4 requires a thermal protection path, and
the pack provides none. Mount the NTC **thermally coupled to the cell** — a
board-mounted thermistor measures board temperature, which is a poor proxy and
partly defeats the JEITA logic. A discrete NTC on short leads taped to the cell
body is better than a nice SMD part on the PCB.

**2. The PCM will not protect your measurement.** Over-discharge trips at ~2.4 V,
but the buck stops at V_SYSMIN = 2.7 V and the FDC1004 is already out of spec
below 3.0 V (rail sags from ~3.4 V). **Firmware must own the low-voltage cutoff**
via the nPM1300 and the fuel gauge. Treat the DW01P purely as a last-ditch safety
net that should never fire in normal service.

**3. Consider dropping VTERM to 4.15 V.** The DW01P's over-charge threshold is
4.25 V ±0.05, so a worst-case part trips at **4.20 V** — exactly our termination
voltage. That risks the PCM cutting the pack off right at end-of-charge, which
looks like a charging fault. Setting the nPM1300's termination to 4.15 V costs a
few percent of capacity, and given that self-discharge is 92 % of the energy
budget (§7), that capacity is worth far less than the reliability.

### Absolute maximum ratings worth pinning to the wall

| Pin group | Max |
|---|---|
| VBUS | 22 V |
| VBAT, VSYS, PVDD, VDDIO | 5.5 V |
| NTC, CC1/CC2, SHPHLD, LED0-2, load-switch pins, VSET, SW1/SW2 | 5.5 V |
| GPIO[0..4], SDA, SCL | VDDIO + 0.3 V |

VBUS tolerates 22 V but **operates** only over 4.0–5.5 V with OVP at 5.5 V. That
distinction drives §4.

---

## 4. Solar input

Solar feeds VBUS through a 5 V pre-regulator, because the nPM1300's VBUS operates
over 4.0-5.5 V.

```
Panel --> 5.0 V pre-regulator --> D5 (Schottky) --> VBUS
```

### How the panel actually becomes 5 V

A bare panel cannot feed VBUS directly. VBUS operates over **4.0–5.5 V** with OVP
at 5.5 V — a 1.5 V window — while a panel's terminal voltage swings with both
illumination and load. It needs active regulation.

**Panel voltage is set by cell count; panel current by area and light.** Indoors,
current collapses (1–10 W/m² vs 1000 outdoors) but voltage holds up reasonably
until you load it. So the panel should be **many small cells in series** — a high
V_OC, low-current part — which keeps its loaded terminal voltage above the
regulator's dropout across a much wider range of light than a few large cells at
the same power.

Target: **V_OC roughly 6–12 V**, regulated down to 5.0 V, then through D5's
~0.3 V drop so VBUS sees ~4.7 V, mid-window. Absolute ceiling is 22 V (VBUS abs
max) so a regulator failure cannot destroy the PMIC.

**Buck vs LDO — the tradeoff that matters here.** A panel is a current-limited
source, which inverts the usual intuition:

- An **LDO** passes whatever current the panel produces, at reduced voltage. Loss
  is (V_panel − 5) × I. With a 6 V panel that is ~17%. Dead simple, no
  startup behaviour to debug, tiny.
- A **buck** converts the excess *voltage* into extra *current*, so it harvests
  meaningfully more from the same panel. Indoors current is the scarce quantity,
  which argues for the buck — but switchers have startup current requirements and
  can motorboat on a weak source, exactly the condition you are in at dawn.

Candidates **[not yet verified — pick one and confirm against its datasheet]**:

| Part | Type | V_IN | I_Q | Note |
|---|---|---|---|---|
| TPS62122 | buck | 2–17 V | ~11 µA | Best harvest; verify start-up on a weak source |
| TPS7A1650 | LDO | up to 60 V | ~5 µA | Simplest, lossy, very wide V_IN |

Pre-regulator requirements:

- V_OUT 5.0 V fixed. After D5's ~0.3 V drop VBUS sees ~4.7 V, mid-window.
- V_IN rating >= 1.5x the panel's V_OC at the coldest expected condition.
- Panel V_OC <= ~12 V keeps the regulator in a sane class. The absolute ceiling
  is 22 V (VBUS abs max), so a pre-regulator failure will not destroy the PMIC.
- I_Q is secondary: with the panel dark the regulator is unpowered and D5
  isolates it from the cell, so it cannot contribute to standing drain.

**Set the VBUS input current limit to match the panel.** The nPM1300 defaults to
IBUS100MA on every reset and after every cable event (§3), so firmware must
re-apply the limit on each boot. That applies to the solar path exactly as it
does to the USB path, and it is the difference between the panel charging and the
panel browning out the input.

Prefer a high-V_OC series-cell panel over a few large cells: more cells in series
holds the loaded terminal voltage up, which keeps the pre-regulator in regulation
across a wider range of light levels.

## 5. Sense front end — FDC1004

### Power gating, the back-powering trap, and a deadlock to avoid

```
VOUT2 (+3V3, always on) ──┬──► nPM1300 LSIN1 ──► LOADSW1 ──► FDC_VDD ──► FDC1004 VDD
                          ├──[4.7k]── SDA
                          └──[4.7k]── SCL
```

**The pullups must be on the always-on +3V3 rail, NOT on the switched FDC_VDD.**

Gating the pullups from the switched rail is the textbook answer to the
back-powering trap, and it is what this design originally did. It is a
**deadlock** here:

1. LOADSW1 is commanded over TWI (or by a GPIO that must itself first be
   configured over TWI — §6.4: *"once configured by host software"*).
2. With the switch off, the pullups are unpowered.
3. I²C is open-drain, so with no pullups the bus can never go high.
4. The PMIC is therefore unreachable, and the load switch can never be turned on.

Cold boot never recovers. The board would be dead on arrival.

**Why putting them on +3V3 is safe here.** FDC1004 absolute maximum ratings
(§5.1) list **SCL and SDA at 6 V, independently of VDD**, in a row separate from
*"at any other pin: VDD + 0.3 V"*. A 6 V rating on a part whose VDD maxes at
3.6 V means there is **no ESD diode from SDA/SCL to VDD**. Holding those pins at
3.3 V while the device is unpowered does not back-power it.

So the trap you flagged in the brief is real for I²C slaves in general, and does
not apply to the FDC1004 on its bus pins. Gate the supply, leave the bus alone.

**Enable the LSOUT active discharge** (`LDSW.LDSWCONFIG`, R_LSPD = 2 kΩ) so
FDC_VDD is actively pulled to ground between wakes instead of floating.

4.7 kΩ rather than 10 kΩ: at 400 kHz 10 k is marginal. These now draw from +3V3
continuously whenever the bus is idle-low, but an idle I²C bus sits high, so the
standing cost is only leakage.

### FDC1004 electrical — verified against SNOSCY5

| Param | Value | Consequence |
|---|---|---|
| Supply | **3.0 min / 3.3 nom / 3.6 max V** | BUCK2 at ±5% gives 3.135–3.465 V — inside spec |
| I_DD conversion | **750 µA typ, 950 µA max** | Matches the power budget assumption |
| I_DD standby | 29 µA typ, 70 µA max | Irrelevant — we hard-gate the rail instead |
| Absolute error | ±6 fF after offset calibration | Your calibration floor |
| Offset drift over temp | 46 fF (−40…125 °C) | Dominates ±6 fF — calibrate at temperature |
| Gain drift | −37.5 ppm/°C | |
| **PSRR** | **13.6 fF/V** | See below — this one bites |
| Input range | ±15 pF, CAPDAC offset to 96.9 pF | |
| **Shield drive** | **400 pF max** | Hard cap on active-shield pour area |
| Excitation | 25 kHz, 2.4 V_pp, 1.2 V DC | |
| f_SCL | 10 kHz … 400 kHz | |

**A buck-ripple gotcha worth acting on.** PSRR is 13.6 fF/V. In Auto mode the
BUCK sits in hysteretic, where VOUT ripple is **50 mV_pp** (Table 21) — that
injects **0.68 fF** of error against a ±6 fF budget, roughly 11% of it, before
you have measured anything. Forced PWM cuts ripple to 5 mV_pp, a 10× improvement.

PWM costs 4.0 mA, but only for the conversion window: 20 ms × 8760 wakes ≈
**0.2 mAh/yr** against a 520 mAh/yr budget. **Force PWM for the measurement, then
return to Auto immediately.** This is exactly the kind of thing the enormous power
slack in §7 is there to buy.

**The rail sags before BUVLO does.** A buck cannot boost, so once V_BAT falls
below roughly 3.4 V the 3.3 V rail follows it down and the FDC1004 drops below its
3.0 V minimum — well before the cell is actually empty. Treat moisture readings as
invalid below that threshold rather than reporting garbage; battery reporting via
the fuel gauge stays valid either way.

### Load switch — verified against §6.4 / Table 22

| Param | Value | Consequence |
|---|---|---|
| VIN_LS range | 1.0 V to VSYS | Datasheet states the input *"can be equal to VOUT1, VOUT2, or any voltage up to VSYS"* — feeding LSIN1 from VOUT2 is explicitly sanctioned |
| RDSON_LS | 200 mΩ @ LSIN = 3.3 V | At ~750 µA that is 0.15 mV of droop. Irrelevant |
| I_LS max | 100 mA | 100× headroom |
| t_SS soft start | 1.8 ms (25 mA limit, 10 µF, 0→5 V) | Faster with our 1 µF. Budget ~1 ms before the FDC1004 rail is valid |
| IQ_LS | **60 nA** extra while enabled | Only during the wake window. Nothing |
| Default state | **OFF** | Safe: the FDC1004 is unpowered until firmware asks |

**Enable the LSOUT active discharge.** `LDSW.LDSWCONFIG` switches in a 2 kΩ
pull-down (R_LSPD) on LSOUT1. Without it, FDC_VDD floats between wakes instead of
being driven to ground — and a floating rail on a part whose ESD diodes tie back
to the I²C bus is exactly the condition you were trying to avoid. Turn it on.

### FDC1004 — pinout verified against TI SNOSCY5 Table 4-1

Package: **VSSOP-10 (DGS)**, `Package_SO:MSOP-10_3x3mm_P0.5mm`. The WSON (DSC)
variant also exists with a DAP that must tie to GND; the VSSOP has no exposed pad
and is far easier to hand-assemble for a prototype. Nothing here dissipates.

| Pin | Name | Type | Net |
|---|---|---|---|
| 1 | SHLD1 | Analog | SHLD |
| 2 | CIN1 | Analog | SENSE1 |
| 3 | CIN2 | Analog | SENSE2 |
| 4 | CIN3 | Analog | open — datasheet: *"If not used, leave this pin as an open circuit"* |
| 5 | CIN4 | Analog | open, same |
| 6 | SHLD2 | Analog | SHLD |
| 7 | GND | Ground | GND |
| 8 | VDD | Power | FDC_VDD |
| 9 | SCL | Input | SCL |
| 10 | SDA | I/O | SDA |

There is **no address pin** — the I²C address is fixed, so the FDC1004 and the
nPM1300 coexist on one bus only because their fixed addresses differ. Confirm
before committing to a shared bus.

Supply current and voltage range are now verified — see the electrical table above.

### Ambient RH/T — SHT45-AD1F

Added primarily as a **compensation input**, not a feature. Verified against the
SHT4x datasheet v7.1.

| Param | Value |
|---|---|
| Part | **SHT45-AD1F** — ±1.0 %RH, **±0.1 °C**, PTFE membrane |
| Supply | 1.08–3.6 V (keeps working after the FDC1004 has dropped out) |
| I_DD idle | **80 nA** typ, 1.0 µA max @ 25 °C |
| I_DD measuring | 320 µA typ, 500 µA max |
| Measurement time | 6.9 ms typ high-repeatability (1.3 ms low) |
| Power-up | 0.3 ms typ, 1 ms max |
| I²C address | **0x44** |
| Package | DFN-4 1.5×1.5×0.5 mm, 0.8 mm pitch |
| Footprint | `Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad` |

**Why temperature accuracy is the spec that matters.** Two error terms feed the
moisture reading:

- FDC1004's own offset drift: 46 fF over 165 °C = **0.28 fF/°C**
- Water's relative permittivity: falls ~0.4 %/°C, so on a 5–15 pF soil reading
  that is **20–60 fF/°C** — roughly 100× larger

The soil term dominates completely, so sensor temperature accuracy sets the
residual:

| T accuracy | Residual moisture error | vs the ±6 fF calibrated floor |
|---|---|---|
| ±0.1 °C (SHT45) | 2–6 fF | at or below the floor |
| ±0.2 °C (SHT40/41) | 4–12 fF | comparable |
| ±0.48 °C (SHT43) | 10–29 fF | temperature becomes the dominant error |

SHT43 is disqualified on this despite sitting in the same price and power class.
RH accuracy barely matters by comparison — ±1.8 %RH is only ~±0.05 kPa of VPD
error at 22 °C — so pay for temperature precision, not humidity precision.

**It must sit on the always-on +3V3 rail, not on gated FDC_VDD.** Table 6 rates
every pin at **VSS − 0.3 V … VDD + 0.3 V**, with no independent I/O rating. An
unpowered SHT4x with the bus pull-ups holding SDA/SCL at 3.3 V would violate
absolute maximum on every sleep cycle. This is the exact opposite of the
FDC1004 (§5.1 there rates SCL/SDA to 6 V regardless of VDD) — the two parts sit
on the same bus and have opposite tolerance for being gated. Cost of leaving it
powered: 80 nA ≈ **0.7 mAh/yr** out of 520.

**Layout constraint, easy to miss.** §5.3: *"Soldering of the central die pad, as
well as an exposed copper pad underneath it, is not recommended... due to it
acting as a heat sink which prevents the heater from functioning."* And: *"There
shall be no copper under the sensor other than at the pin pads."* The KiCad
`_NoCentralPad` footprint variant already reflects this — do not substitute a
generic DFN-4 with a thermal pad.

**Membrane vs cover.** The `-xD1F` PTFE membrane is the permanent protection:
100 µm, >99.99 % filtration at 200 nm, IP67, and the RH response time is
unaltered. The `-xD1P` "protective cover" is a *removable* polyimide foil that
exists only to mask the sensor opening during conformal coating and is peeled off
afterwards — not protection in service. For soil dust and watering splash, take
the membrane.

**Built-in heater** (20 / 110 / 200 mW, up to 60 mA) can burn off condensation —
useful in a humid plant environment, but it is a 60 mA load, so short pulses only
and never on battery-critical wakes.

Decoupling: 100 nF on VDD, per the datasheet's typical application circuit.

### Battery voltage — the divider is gone

The nPM1300 has a **10-bit ADC that measures battery voltage, battery current,
VBUS voltage, and die temperature** natively, read over I²C. This deletes:

- the resistor divider,
- its 1.7 µA standing drain (15 mAh/yr),
- the abs-max hazard where a GPIO-gated divider floats the sense node to full
  V_BAT (4.2 V) against a 3.6 V pin limit,
- the SAADC configuration and settling-time work.

On top of that you get Nordic's **fuel gauge algorithm** running on the host,
giving a real state-of-charge estimate rather than a voltage guess. For BTHome
battery reporting that is a straight upgrade — voltage-to-percentage on a Li-ion
discharge curve is nearly flat through the middle of the range and gives poor
readings.

**[Fuel gauge is a host-side library in NCS; confirm it is available for
nRF54L15 in your NCS version and check its RAM/flash cost against a design that
cold-boots every hour.]**

---

## 6. Proposed pin assignment

Verified against the nRF54L15 datasheet v1.0, QFN48 (QFAA) pin assignment
table (§10.1.4) and the port capability rules (§8.8.3, Table 40).

| Signal | nRF pin | Port | Why this pin |
|---|---|---|---|
| I²C **SCL** | 39 | P1.11/AIN4 | **must be a dedicated clock pin** (Table 77) |
| I²C **SDA** | 38 | P1.10 | adjacent to the clock pin, same port |
| PMIC interrupt | 23 | P0.00 | must be wake-capable — see below |
| SWO (trace) | 18 | P2.07 | dedicated trace pin |
| SWDIO / SWDCLK / RESET | 25 / 26 / 30 | — | SWD header |

**Three rules from the datasheet that constrain this, all of which the earlier
guess violated:**

1. **TWIM/TWIS SCL must be on a dedicated clock pin.** Table 77 lists SCL as
   "Clock pin required: Yes". On QFAA the clock pins are **P0.03, P0.04, P1.03,
   P1.04, P1.08, P1.11, P1.12, P2.01, P2.06**. P1.09 — the earlier choice — is
   not one of them.
2. **Peripherals cannot mix pins from different ports** (§8.8.3). SDA and SCL
   must both be on P1.
3. **P2 cannot wake the system.** Table 40: P2 has no wake capability, no
   SENSE/DETECT, and no GPIOTE. PMIC_INT on P2.00 — the earlier choice — could
   never wake the MCU from System OFF. It is now on P0.00, in the low-power
   domain, which has all three.

SDA sits physically adjacent to SCL (pins 38 and 39) because the datasheet
requires the data signal to "use pins close to the clock pin" so the internal
path delays match, and asks for short traces of identical length on the PCB.

P1.03 was avoided as a clock pin because it is NFC2 and **NFC is enabled from
reset** — using it as GPIO means disabling NFC in the PADCONFIG register first.

SWD header: SWDIO, SWDCLK, RESET, 3V3, GND. RESET keeps the R1/C5 filter from §2.

---

## 7. Power budget

### Result

**Cell is an Adafruit 258 — 1200 mAh, 34 × 62 × 5.0 mm.** The 10 mm 103450 does
not fit the Hammond 1551WK height budget; see LAYOUT.md §9 and BOM.md for the
full fit table.

| | Adafruit 258 (fitted) | 103450 (for comparison) |
|---|---|---|
| Nominal capacity | 1200 mAh | 2000 mAh |
| Total annual charge draw | ≈ 331 mAh/yr | ≈ 523 mAh/yr |
| Usable capacity | ≈ 1140 mAh | ≈ 1900 mAh |
| **Projected runtime** | **≈ 3.45 years** | ≈ 3.6 years |

### Breakdown, at 1200 mAh

| Item | Current | mAh/yr | % | Scales with capacity? |
|---|---|---|---|---|
| Cell self-discharge | — | 288 | 87% | **yes** |
| Cell PCM quiescent | ~3 µA | 26 | 7.9% | no |
| nPM1300 + nRF54L15 System OFF | ~1.5 µA | 13 | 3.9% | no |
| SHT45 idle (always powered) | 80 nA | 0.7 | 0.2% | no |
| Hourly wake cycles | — | 3 | 0.9% | no |

### Why halving the cell costs only 7%

Self-discharge is 2%/month **of whatever capacity is in there**, so it shrinks
with the cell. Only the 42.8 mAh/yr of fixed terms stay put:

```
runtime = 0.95·C / (0.24·C + 42.8)      C in mAh, result in years
```

| C | 2000 | 1200 | 1000 | 800 | 600 | 300 |
|---|---|---|---|---|---|---|
| years | 3.63 | 3.45 | 3.36 | 3.24 | 3.05 | 2.48 |

Two things fall out of that expression. **There is a ceiling at 0.95/0.24 =
3.96 years** — no cell that fits this enclosure gets meaningfully past 3.6, so
the 103450 was buying almost nothing. And the result is robust to the
self-discharge figure: at 1%/month the 2000→1000 penalty is 13%, at 3%/month it
is 5%. Worse self-discharge makes cell size matter *less*.

Li-ion calendar ageing is 3–5 years at indoor storage regardless of cycling, so
3.4 years already meets the cell's own service life.

**A primary coin cell is not a cell swap.** CR2032 self-discharges at ~1%/*year*
rather than 2%/month, which on this budget would be ~11 years — but the nPM1300's
VBAT is a charger output and cannot take a primary cell, and a CR2032 sits at
2.9–2.5 V for most of its discharge against the FDC1004's 3.0 V minimum (§5),
which a buck cannot boost. It needs a different power architecture, not a
different part.

The combined PMIC-plus-sleeping-MCU figure needs a caveat. Table 3 gives
I_QBAT = 800 nA for one BUCK in Auto at **no load**. Figure 3's efficiency curve
suggests ~70% at 1 µA of load. Depending on which you propagate, the total lands
between **1.1 and 1.7 µA**. I have budgeted 1.5 µA. Measure it — it is easy to
measure and it is 2.5% of budget either way, so do not spend time modelling it.

Also from Figure 5: **I_QBAT rises steeply above 25 °C**, roughly 800 nA at 25 °C
to 4.5–5.6 µA at 85 °C. Indoors at 20–25 °C you are on the flat part of the curve.
A device left in a hot conservatory would do materially worse.

### The conclusion that should drive your firmware effort

**The wake cycle is 0.6% of the budget. The cell is 92%.**

Your 300 ms awake target is not worth contorting the firmware for. At 3 mA
average, going from 300 ms to a full **3 seconds** per wake costs 22 mAh/yr —
about 4% of budget, taking runtime from 3.6 to 3.5 years. Spend that slack on
generous FDC1004 settling and reliable PMIC configuration instead of chasing
milliseconds.

If you want more than 3.6 years, the only lever that matters is the cell.

### Assumptions — check these

1. **Self-discharge 2%/month.** Still 85% of the budget and still the number I am
   least sure of. Quality Li-ion is quoted 1.5–3%/month at 20 °C, rising sharply
   with temperature and state of charge. At 1000 mAh the 1–3%/month band spans
   **5.8 down to 2.4 years**. **Get this from your cell's datasheet** — it is
   worth more than any layout decision on this board.
2. **PCM quiescent ~3 µA.** Typical for a small protection module, unverified for
   your cell. 1–10 µA is a normal range. At 1000 mAh this is now 9% of the
   budget — second only to self-discharge, and bigger than the entire
   electronics draw. Worth measuring on whatever protected cell you buy.
3. **nPM1300 + nRF sleep 1.5 µA**, per the caveat above.
4. **Wake cycle 300 ms at 3 mA average**, plus PMIC I²C configuration. A composite
   estimate, not measured. At 0.6% of budget, being wrong by 5× changes nothing.
5. **8760 wakes/yr** (hourly).
6. **Usable capacity 95% of nameplate**, so 1140 mAh on the Adafruit 258. At these tiny
   currents you will get close to nameplate.
7. **20–25 °C ambient.** Indoor, and this matters more than it did before — see
   the I_QBAT temperature curve.
8. Assumes the device **never** sees USB and solar contributes zero. Any charging
   at all extends this indefinitely.

---

## 8. Open items

- Confirm nRF54L15 peripheral-to-port binding for §6.
- I²C addresses all confirmed distinct: **FDC1004 0x50** (SNOSCY5 §6.5.1),
  **nPM1300 0x6B**, **SHT45-AD1F 0x44**. One bus, no split needed.
- Cell datasheet: self-discharge rate, PCM quiescent current, NTC availability.
- Select the solar pre-regulator and the panel (V_OC, loaded voltage at
  indoor irradiance).
- Confirm nPM1300 driver + fuel gauge availability in your NCS version.
- Find the nPM1300 hibernate wake-timer maximum timeout — not yet checked. Only
  matters if you later want the PMIC to power-cycle the MCU rather than using
  System OFF; §7 says that would save ~8 mAh/yr, which is not worth it.
- Antenna selection and layout constraints — separate document.

---

## 9. Why the charger changed

Recorded so the decision is not relitigated later.

**Standing drain, like for like:**

| | |
|---|---|
| BQ25185 (4 µA) + TPS7A02 (25 nA) + nRF sleep 0.9 µA | ≈ 4.9 µA |
| nPM1300 (800 nA, one BUCK Auto) + same load | ≈ 1.5 µA |

A genuine 3× improvement — but worth only **~3 months** (3.36 → 3.64 years),
because self-discharge is 92% of the budget. **The power saving was not the
reason.** The reason was integration:

| Deleted | Replaced by |
|---|---|
| Battery divider, its 15 mAh/yr, its abs-max trap, the SAADC work | Built-in 10-bit ADC |
| Discrete PMOS gating FDC_VDD | LOADSW1 |
| R_ISET, R_ILIM/VSET | I²C-configurable 32–800 mA, runtime-adjustable |
| 2× 5.1 kΩ CC resistors | Internal R_d pull-downs on CC1/CC2 |
| Voltage-only battery estimate | Fuel-gauge SoC algorithm |
| STAT LED circuit and its 250 mV abs-max margin | 3 dedicated LED drivers |
| Fixed 3.0 V BUVLO with no options | Configurable thresholds |
| 68.3 °C/W thermal path | 24.2 °C/W (QFN32) |

**What it cost:** VBUS narrowed from 3.6–18 V to 4.0–5.5 V, so the solar input now
needs a pre-regulator (§4), and pack protection circuitry became mandatory rather
than optional (§3).

---

## Sources

- [nPM1300 Product Specification v1.3](https://www.nordicsemi.com/Products/nPM1300) (local: `nPM1300_PS_v1.3.pdf`) — Table 3 (system electrical spec), Table 4 (abs max), Tables 6–9, §3.4, §3.5, §5.2, §6.1
- [nRF54L15 reference circuitry, circuit configuration 1 for QFN48 (QFAA)](https://docs.nordicsemi.com/r/bundle/ps_nrf54l15/page/chapters/ref_circuitry.html-concept_refcircuit_config_1) — Tables 1 and 2, grounding notes
- [nRF54L15 LFXO parameters](https://docs.nordicsemi.com/bundle/ps_nrf54L15/page/_tmp/nrf54l15/autodita/OSCILLATORS/parameters.low_frequency_crystal_oscillator.html)
- [nRF54L15/L10/L05 datasheet v1.0](https://www.mouser.lt/datasheet/3/926/1/nRF54L15_nRF54L10_nRF54L05_Datasheet_v1.0.pdf) — System OFF current figures
- [Nordic DevZone: configuring internal load capacitance for the 32 MHz crystal on nRF54L](https://devzone.nordicsemi.com/f/nordic-q-a/120541/how-to-configure-internal-load-capacitance-for-32-mhz-crystal-on-nrf54l-ncs-2-9-0)
- [BQ25185 datasheet SLUSF65A](https://www.ti.com/lit/ds/symlink/bq25185.pdf) — superseded, retained for the §9 comparison
