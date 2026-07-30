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
                                                  └──► VBAT ──► 103450 Li-ion 2000 mAh
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

| Des | Value | Description | FP | Net / pin |
|---|---|---|---|---|
| U1 | nRF54L15-QFAA | SoC | QFN-48 | — |
| L1 | 4.7 µH | Inductor, 120 mA, ±20%, 650 mΩ | 0603 | DCC (46) → VDD |
| C1 | 2.2 µF | X6T, ±20%, 2.5 V | 0201 | DECA (43) |
| C2 | 2.2 µF | X6T, ±20%, 2.5 V | 0201 | DECD (45) |
| C12 | 10 nF | X7R, 6.3 V | 0201 | DECA (43) |
| C3 | 10 µF | X6S, ±20%, 6.3 V | 0402 | VDD bulk |
| C4, C7, C8, C10 | 100 nF | X7R, ±10% | 0201 | one per VDD pin (10, 22, 36, 47/48) |
| FB1 | 120 Ω @ 100 MHz | Ferrite bead, 200 mA, 500 mΩ max | 0201 | VDD feed |
| R1 | 1 kΩ | ±1%, 0.05 W | 0201 | RESET (30) series |
| C5 | 2.2 nF | X7R, ±10%, 10 V | 0201 | RESET (30) to GND |
| X1 | 32.768 kHz | **C_L = 9 pF, total tol ±20 ppm** | 2012 | XL1 (1) / XL2 (2) |
| X2 | 32 MHz | **C_L = 8 pF, total tol ±40 ppm** | 2016 | XC1 (34) / XC2 (35) |

### Crystal load capacitance — your explicit question

**No discrete load caps on either crystal.** Nordic's reference BOM lists none on
XC1/XC2 or XL1/XL2, because both oscillators have internal trimmable banks:

- **HFXO:** internal caps **4 pF to 17 pF in 0.25 pF steps**. X2's C_L = 8 pF is
  inside that range.
- **LFXO:** internal caps to a maximum of **18 pF in 0.5 pF steps**. X1's
  C_L = 9 pF is inside that range.

You specify the crystal's C_L in part selection and match it in firmware via the
INTCAP trim registers. The matching happens in software, not in copper. Budget a
trim step at bring-up: measure the 32 MHz carrier and adjust INTCAP until the
frequency error is centred.

**ppm requirements.** BLE requires ±50 ppm on the active carrier. X2 at ±40 ppm
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
| C13 | 3.9 pF | C0G ±0.25 pF, 50 V, 0201 |

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

Pre-regulator requirements **[specific part selection in progress]**:

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

Starting point. **[Confirm every one against the nRF54L15 pin-mux / peripheral
port table — on nRF54L, peripheral instances bind to particular GPIO ports, so
these are not freely interchangeable.]**

| Signal | nRF pin | Port | To |
|---|---|---|---|
| I²C SCL | 37 | P1.09 | nPM1300 SCL + FDC1004 SCL |
| I²C SDA | 38 | P1.10 | nPM1300 SDA + FDC1004 SDA |
| PMIC interrupt | 11 | P2.00 | nPM1300 GPIO (host IRQ) |
| SWDIO / SWDCLK / RESET | 25 / 26 / 30 | — | SWD header |

Both the PMIC and the FDC1004 sit on one I²C bus. Different addresses, no
conflict. Note the bus pullups are on the *switched* FDC_VDD rail per §5 — which
means the PMIC is only reachable while LOADSW1 is on. **If that is not acceptable,
split into two buses or move the pullups to 3V3 and pre-drive SDA/SCL low before
gating.** Decide this before layout; it is a real constraint created by the
elegant pullup trick.

The battery-sense pin, FDC power-gate GPIO, STAT inputs, and CE inhibit from the
previous revision are all gone — absorbed into the PMIC.

SWD header: SWDIO, SWDCLK, RESET, 3V3, GND. RESET keeps the R1/C5 filter from §2.

---

## 7. Power budget

### Result

| | |
|---|---|
| Total annual charge draw | **≈ 520 mAh/yr** |
| Usable capacity | ≈ 1900 mAh |
| **Projected runtime** | **≈ 3.6 years** |

### Breakdown

| Item | Current | mAh/yr | % |
|---|---|---|---|
| Cell self-discharge | — | 480 | 92% |
| Cell PCM quiescent | ~3 µA | 26 | 5.0% |
| nPM1300 + nRF54L15 System OFF | ~1.5 µA | 13 | 2.5% |
| Hourly wake cycles | — | 3 | 0.6% |

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

1. **Self-discharge 2%/month.** Dominates everything and is the number I am least
   sure of. Quality Li-ion is quoted 1.5–3%/month at 20 °C, rising sharply with
   temperature and state of charge. At 1%/month runtime goes to ~5.9 years; at
   3%/month, ~2.6 years. **Get this from your cell's datasheet.**
2. **PCM quiescent ~3 µA.** Typical for a small protection module, unverified for
   your cell. 1–10 µA is a normal range.
3. **nPM1300 + nRF sleep 1.5 µA**, per the caveat above.
4. **Wake cycle 300 ms at 3 mA average**, plus PMIC I²C configuration. A composite
   estimate, not measured. At 0.6% of budget, being wrong by 5× changes nothing.
5. **8760 wakes/yr** (hourly).
6. **Usable capacity 1900 mAh.** At these tiny currents you will get close to
   nameplate.
7. **20–25 °C ambient.** Indoor, and this matters more than it did before — see
   the I_QBAT temperature curve.
8. Assumes the device **never** sees USB and solar contributes zero. Any charging
   at all extends this indefinitely.

---

## 8. Open items

- Confirm nRF54L15 peripheral-to-port binding for §6.
- **Confirm the FDC1004 and nPM1300 fixed I²C addresses do not collide** — the
  FDC1004 has no address pin, so if they clash the bus must be split.
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
