> 2026-09-09: D8/D9 clamp the protected CIN nets after R30/R31. Both electrodes now occupy all four copper layers, with all-layer SHLD rings closed at the tip. See [probe revision and electrical limits](docs/probe-review-2026-09-09/README.md).

> 2026-09-07: C21/C23 use GRM158R60J226ME01D; D8/D9 have dedicated In1 ground returns. Real board qualification firmware is in `firmware/sensor`. See [implemented reliability changes](docs/reliability-2026-09-07/README.md) for current limits and required measurements.

# nRF Moisture Sensor — Hardware Design

Ezurio BL54L15 453-00001R · nPM2100 (QFN16) · FDC1004 · SHT40 · BTHome v2 over BLE · CR2032

All values below are cited from the source that was checked. Anything marked
**[assumed]** has not been verified and needs your sign-off.

**Revision note.** The requirements changed: this is now board 1 of a two-board
system, a moisture sensor powered by a single user-replaceable CR2032, with
the data emitted as BTHome over BLE. The primary-cell nPM2100 architecture is
the production design; USB-C input, solar input and the rechargeable pack are
deleted from this board. The superseded charging analysis is retained only in
git history for the separate pump-controller board.

---

## 1. Power tree

```
CR2032 ──► Q1 reverse PMOS ──► nPM2100 VBAT ──► BOOST ──► VINT ──► VOUT 3.3 V ─┬─► BL54L15
                                   (SW/L1)                ├─► SHT40 (always on)
                                                          └─► I²C pull-ups (always on)
                    VINT ──► LDOSW ──► +3V3_FDC_SW ──► FDC1004 (gated)
```

One primary cell, no charging path; Q1 provides reverse-polarity protection (§3). The entire
input section of the old design — USB-C, solar pre-regulator and diode, rechargeable
pack, NTC — is deleted with the architecture change.

**VOUT = 3.3 V is a firmware write, not a strap.** The VSET pin selects only the
*startup* voltage: not connected = 3.0 V, grounded = 1.8 V (PS §6.1.1). It is
left not connected. On battery insertion the board comes up at 3.0 V — exactly
the FDC1004's minimum, which is harmless because the FDC1004 is gated off at
that moment (LDOSW defaults OFF) — and firmware then writes `BOOST.VOUT` +
`BOOST.VOUTSEL` to raise the rail to 3.3 V. Registers survive Hibernate (PS
§7.4: "Register content remains") and the SoC's System OFF (the PMIC never
sleeps), so this is one write per battery insertion, not per wake. It must be
redone after a Hibernate_PT wake or a watchdog power cycle, both of which reset
the PMIC.

**There is no OTP.** The nPM2100 has no factory-programmed
configuration option (PS §10.5 lists only package/build variants), so runtime
configuration is mandatory and the battery-insert boot path must configure the
PMIC in a known sequence before any rail-dependent peripheral is enabled.

**Pass-through never engages.** BOOST enters pass-through only when VBAT is
≥ 100 mV above the target VOUT (PS §6.1.2) — 3.4 V at a 3.3 V target, which a
CR2032 never reaches (2.0–3.3 V over its discharge, ngl_002 Table 1). The
converter regulates at every state of charge, so VOUT accuracy is identical
throughout the discharge.

**Boost mode is Auto.** ULP at our µA-level sleep load (IQULP 300 nA typ),
LP/HP as load rises, all automatic (PS §6.1.2, Figure 4). Forced High Power is
applied transiently around each capacitance measurement — see §5, where the
LP/ULP ripple injects ~0.95 fF of error through the FDC1004's PSRR. Forcing HP
costs 7.2 mA for ~20 ms, ≈ 0.35 mAh/yr.

**VINT carries no external load** (PS Table 22: "No external load is allowed")
— it exists for the boost output capacitor and feeds LDOSW internally. Bulk
capacitance belongs on VINT, not VOUT (nwp_058 §3.2), and CVOUT is capped at
15 µF effective (PS Table 10).

---

## 2. Ezurio BL54L15 module and external support

U1 is **453-00001R**, the 14 × 10 mm PCB-antenna BL54L15. The µ module
and MHF4 external-antenna variants are not substitutes. The verified 39-pad
symbol, footprint coordinates, all-layer keepouts and assembly plan are in
[the integration record](docs/bl54l15/README.md).

The module integrates the nRF54L15, its DC/DC inductor/filter and internal-rail
decoupling, 32 MHz crystal, RF matching and PCB antenna. The oscillator load
banks are inside the SoC and still require firmware configuration. No host
DCC/DECD/DECA/DECRF, XC1/XC2 or RF feed is exposed.

| Ref | External support retained | Connections |
|---|---|---|
| C3 | 10 µF nominal, 25 V X5R, standard 0603 (C96446) | U1.26 VDD_nRF to GND |
| X1 | CM8V-T1A, 32.768 kHz, CL 7 pF, ±20 ppm | U1.25 XL1 → X1.1; U1.24 XL2 → X1.2 |
| R1 / C13 | 1 kΩ series reset / 3.9 pF C0G filter, standard 0402 | SWD_RST → R1 → NRESET; C13 to GND; U1.7 NRESET |
| R22 / R23 | Existing 4.7 kΩ I²C pull-ups | SDA / SCL to VOUT |
| J4 | Existing Tag-Connect programming contacts | SWDIO, SWDCLK, reset, SWO, VDD, GND |

X1 is retained for timed System OFF/GRTC wake. No discrete crystal load
capacitors are fitted. **The old claim that the firmware capacitance parameter
is simply the crystal's 7 pF CL is superseded:** current Nordic guidance defines
it as the internal capacitor value. Select internal loading, calculate the
series-equivalent load including module/host parasitics, and measure startup
and frequency. A 12 pF bank target is an initial estimate for 2 pF additional
capacitance per leg, not a validated trim. See
[firmware port notes](firmware/BL54L15-port.md). The old X2 load value must not
carry over to the module's integrated HFXO.

**Supply qualification is open.** Ezurio specifies at most 10 mV ripple/noise
for undisturbed radio operation. nPM2100 LP/ULP ripple is typically 70 mVpp;
force HP for radio activity as well as FDC measurements and measure at U1.26.
HP mode alone is not proof of compliance. At nominal values, directly attached
host VOUT capacitors total 12.3 µF (C3+C25+C27), before module input capacitance;
verify the nPM2100's 0.7–15 µF effective VOUT range over bias/tolerance including
the module. Do not add bulk capacitance indiscriminately. Include the switched FDC rail
capacitance when assessing the enabled load-switch state. Keep the existing
3.3 V architecture; prototype validation may identify a required supply-filter
change. This layout is a routing handoff, not a fabrication release.

---

## 3. PMIC — nPM2100

**Package: QFN16 4×4 mm, part `nPM2100-QEAA`.** Not the WLCSP — that variant
is sensitive to visible and near-IR light (PS §5.2) and its GPIO0/SYSGDEN pins
cannot be routed without microvias on our stackup (nwp_058 §4.1). QFN16 also
has the better thermal path (R_θJA 40 °C/W vs 58 °C/W, PS Tables 8–9), which
matters little at our dissipation but costs nothing. Order code
`nPM2100-QEAA-R7`, MOQ 1500 from Nordic (PS Table 38) or singles from a
distributor.

The design follows Nordic's **reference circuit Configuration 2 — the CR2032
case** (PS §9.3.2): VSET not connected, CVINT 22 µF, LDOSW fed off VINT. One
deliberate deviation: Nordic's configuration runs LDOSW as an LDO at reduced
voltage; we run it as a **load switch passing the boost rail** to +3V3_FDC_SW,
because the FDC1004 wants 3.3 V, not ≤ 3.0 V (§5).

### Pinout — verified against PS Table 22 (QFN16)

| Pin | Name | Net | Notes |
|---|---|---|---|
| 1 | VSET | — (NC) | internal pull-up to VINT; NC = 3.0 V startup. No strap resistor |
| 2 | SW | /SW | boost switch node → L10 |
| 3 | VBAT | /VBAT | from the CR2032 holder |
| 4 | SHPHLD | — (NC) | ship/wake button input; unused — see below |
| 5 | GPIO0 | /PMIC_INT | event interrupt output → nRF P0.00 (§6) |
| 6 | SDA | /SDA | TWI data, external pull-up to VOUT |
| 7 | SCL | /SCL | TWI clock, external pull-up to VOUT |
| 8 | SYSGDEN | GND | grounded: boot monitor disabled at startup |
| 9 | GPIO1 | — (NC) | spare: boost-force / LDOSW pin-control option |
| 10 | PG/RESET | /SWD_RST | open-drain, internal pull-up to VINT; watchdog host-reset output — joins the nRF RESET net |
| 11 | AVSS2 | GND | |
| 12 | LSOUT/VOUTLDO | /+3V3_FDC_SW | load switch output → FDC1004 |
| 13 | VOUT | /+3V3 | boost output for the load |
| 14, 15 | VINT | /VINT | boost decoupling only — no external load |
| 16 | PVSS | GND | power ground, boost return |
| EP | AVSS1 | GND | |

**SHPHLD stays unconnected.** Ship mode (35 nA) exists for factory storage with
the cell installed; this product ships without a cell, and battery removal is
the off switch. The pin may be left NC (PS Table 22), and its absolute maximum
is only **1.9 V** (PS Table 5) — nothing on this board may ever touch it. If a
user button is wanted later, it is a button to ground on this pin (2 s press =
ship, press = wake, 10 s = reset, PS Table 17) and costs one enclosure hole.

**PG/RESET joins the nRF RESET net.** It is open-drain with an internal pull-up
to VINT (PS Table 22) — wired-OR compatible with the R1/C13 filter and the SWD
connector already on that net (§2, §6). This lets the PMIC watchdog issue a host
reset, or in power-cycle mode reset the SoC *and* the PMIC — a stronger recovery
path than the SoC's own watchdog for a device that cold-boots hourly with the
radio up.

### Configuration

| Function | Setting | Notes |
|---|---|---|
| BOOST VOUT | 3.3 V, TWI-set after startup | VSET NC gives 3.0 V at cold start; see §1 |
| BOOST mode | Auto (ULP/LP/HP/PT automatic) | forced HP around conversion and all radio activity — §§2,5 |
| LDOSW | **Load switch**, TWI-enabled per wake | OFF by default (PS §6.2); active discharge built in |
| Watchdog | configurable: host reset or power cycle | covers hangs the SoC's own WDT cannot see |
| Boot monitor | disabled — SYSGDEN grounded | otherwise arms 10 s after every timer wake (PS §7.2.3) and must be stopped in software; the configurable watchdog replaces it |
| Ship / Break-to-wake | unused | battery-out is the off switch |
| TWI | address 0x74, 100 kHz–1 MHz | pull-ups to VOUT (PS §7.6) |

### Support components — PS §9.3.2 (Configuration 2) and nwp_058 §3

| Des | Value | Description | FP | Net |
|---|---|---|---|---|
| U2 | nPM2100-QEAA | PMIC | QFN16 4×4 | — |
| L10 | Murata DFE201210U-2R2M=P2, 2.2 µH | **I_sat 2 A, DCR 228 mΩ max, ±20%** — no other inductance permitted (nwp_058 §3.1) | 2.00 × 1.20 mm | SW (2) → protected VBAT (3) |
| C21 | 22 µF | X5R 6.3 V ±20% | 0402 | VBAT (3) |
| C22 | 1 nF | X7R 50 V, FH 0402B102K500NT | standard 0402 | VBAT (3) |
| C23 | 22 µF | X5R 6.3 V ±20% | 0402 | VINT (14/15) |
| C24 | 1 nF | X7R 50 V, FH 0402B102K500NT | standard 0402 | VINT |
| C25 | 2.2 µF | X5R 6.3 V ±20% | 0402 | VOUT (13) |
| C26 | 1 µF | local decoupling at the FDC1004 | 0402 | +3V3_FDC_SW (12) |

Capacitor notes, from nwp_058 §3.2–3.4 and PS Table 10:

- **Effective capacitance is what matters.** CVBAT and CVINT each need
  ≥ 3.5 µF *effective*, CVOUT 0.7–15 µF effective, after DC bias, tolerance and
  temperature. A 10 µF 0402 X5R at 3 V bias is not 10 µF — check the derating
  curve for the specific part ordered.
- **The 1 nF caps are the RF decoupling** Nordic specifies for RF-sensitive
  applications (nwp_058 §3.2/§3.3). This board has a 2.4 GHz radio and a 25 kHz
  capacitive front end; both are fitted.
- **C26 on +3V3_FDC_SW:** load-switch mode needs no output capacitor for the switch
  itself (nwp_058 §3.4), but the FDC1004 still gets local decoupling. 1 µF was
  already the value on the old gated rail (§5); the hourly recharge cost is
  negligible.
- **The inductor is not a free choice.** 2.2 µH ±20% only — other values break
  the control loop (nwp_058 §3.1). Inductor peak current in hysteretic ULP/LP is
  typ. 150 mA with startup transients above that, hence the 550 mA I_sat floor.
  Candidates with measured efficiency on the EK (nwp_058 Tables 4–5, VBAT
  2.9 V → VOUT 3.3 V): **Murata DFE201210U-2R2M=P2** (2012, 91.9% at 100 µA,
  94.7% at 120 mA), TDK MLP2016H2R2MT0S1 (2016, 91.5%/95.0%).
  The Murata part is locked. Its board footprint uses two 0.55 × 1.20 mm pads
  on 1.45 mm centres, a 0.90 mm inner gap, and a 2.70 × 1.90 mm courtyard.

### Cold start, EOL pulses, and the reservoir question

Cold start requires the battery to supply **≥ 10 mA typ during startup** (PS
Table 4) — trivial for a fresh CR2032 (10–25 Ω ESR), marginal at end of life
where ESR rises steeply at the knee (ngl_002 Table 1: CR2032 ESR 10–80 Ω over
the discharge). Two consequences:

1. **The TX pulse rides on CVBAT.** Nordic's own CR2032 BLE test (nwp_058 §3.5)
   measured **+11.6% battery life from 100 µF added at VBAT** and +17.9% from
   100 µF at both VBAT and VINT — input-side capacitance cuts the I²·R ESR loss
   during pulses. The reference circuit ships 10 µF + 1 nF at VBAT; the 100 µF
   upgrade is a bring-up measurement to make, not a default to fit. Leave a
   footprint for it if placement allows.
2. **A deeply discharged cell may fail to restart.** VBATCOLD_START is 0.8 V
   *loaded*. The ADC's VOUT droop detector plus the fuel gauge's low-SoC output
   give firmware the signal to degrade gracefully — shorter wakes, then stop
   advertising — rather than brown-out looping at the cell's knee.

### Reverse battery and ESD — implemented 2026-09-04

The former accepted reverse-insertion risk is superseded by Q1 (DMG2305UX-7).
Drain pin 3 connects to raw BT1 positive, source pin 2 to VBAT, gate pin 1 to GND.
C21/C22 remain on protected VBAT. D1/D2 clamp raw/protected battery inputs;
D3–D7 protect the programming interface; D8–D10 cover sense/shield connections.
R30/R31 add 5.1 kohm sense-input isolation and R32–R35 add 100 ohm debug isolation.
See [protection implementation and qualification limits](docs/protection/README.md).

BT1 is Lian Xin CR2032-BS-6, LCSC C22363833, with positive pad 1 on the left
and negative pad 2 on the right in the footprint's unrotated top view. D1 is
on F.Cu beside the positive contact. The part-specific stepped courtyard
preserves at least 0.25 mm body clearance; Q1 clears that courtyard. No PTC or sustained-OVP
cutoff is fitted. Prototype ESD, leakage, cold-start and sensing validation are
still required. A single PMOS is not guaranteed reverse-current isolation from
an externally powered rail into the primary cell; J4 remains a voltage reference.

### Hibernate vs System OFF — the wake architecture

The nPM2100 can own the wake cycle itself: Hibernate mode (boost holds VINT,
VOUT discharged, LDOSW optionally alive) draws **320 nA typ with the timer
running** at VINT = 1.8 V (PS Table 4; 175 nA in Hibernate_PT), and the wakeup
timer spans up to **3 days** at ±3% typ accuracy (PS Table 16) — an hourly cycle
fits in one shot.

This design keeps the **SoC System OFF + GRTC wake** architecture:

| | System OFF + GRTC (chosen) | PMIC Hibernate timer |
|---|---|---|
| Battery draw between wakes | ~1.5 µA (nRF SO + GRTC/LFXO, PMIC 300 nA, SHT40 80 nA) | 320 nA typ, PMIC only |
| Wake timing accuracy | ±20 ppm (LFXO) | ±3% typ, ±20% over temperature |
| Fuel gauge state | survives in retained RAM | lost with VOUT — persist to RRAM/flash every wake (nan_048 §4.1) |
| PMIC configuration | written once per battery insert | re-written after every Hibernate_PT wake |
| Firmware | already implemented and DK-verified | same cold-boot model, new driver path |

The ~1.2 µA difference is ~10 mAh/yr on a budget where the cell's own shelf
life binds first (§7) — not worth re-architecting a working, verified wake path,
and the fuel-gauge state persistence tips it further (nan_048 §4.1:
reinitializing from scratch each wake degrades accuracy). The hibernate path
stays available in firmware at any time with zero schematic changes; it is the
fallback if the measured sleep current disagrees with the budget.

---

## 4. Solar input — deleted with the architecture change

This board is coin-cell powered now. The solar branch (Voltaic P126 panel,
TPS7A1650 pre-regulator, D5, J3) and the USB-C input belong to the charging
architecture this board no longer has.

Board 2 — the pump controller, which is battery *or* mains powered — inherits
all of it. The superseded analysis (panel selection, pre-regulator comparison,
the barrel-jack placement argument, the 100 mA VBUS current-limit firmware
dance) is preserved in this file's git history at commit 1753c18, alongside
the archived charging-design datasheets. Do not carry any of it forward into
this board's BOM or layout.


## 5. Sense front end — FDC1004

### Dedicated FDC bus and power gating

```
+3V3 ── R22/R23 ── SDA/SCL ── TWIM22 (P1.10/P1.11), nPM2100, SHT40
+3V3_FDC_SW ── R36/R37 ── FDC_SDA/FDC_SCL ── TWIM20 (P1.05/P1.04), FDC1004
```

The FDC now has a separate hardware I²C bus: U1.22/P1.05 is FDC_SDA and
U1.23/P1.04 is FDC_SCL. R36/R37 are 4.7 kΩ pull-ups to its switched supply.
R22/R23 remain on always-on +3V3 so the PMIC can enable LDOSW at cold boot.
Switching the PMIC's own pull-ups would prevent that command from reaching it.

The dedicated pins must have no internal pull-ups and must be disconnected
while FDC power is off. The sensor firmware starts TWIM20 suspended, resumes
it for each transfer after power-up, and returns it to its sleep pinctrl state
after each transfer, including failures. It verifies the bus is suspended
before disabling LDOSW and entering System OFF. SPI20/UART20 remain disabled.

This removes the shared bus's always-on pull-up path into the unpowered FDC.
FDC1004's independent 6 V SDA/SCL absolute maximum rating does not establish
powered-off leakage. Measure rail voltage and battery current with FDC power
off, including main-bus activity, reset and sleep/wake transitions.
See [wiring update and routing handoff](docs/fdc-bus-update-2026-09-09/README.md).

**The LSOUT active discharge is built in.** PS §6.2: *"The LSOUT/VOUTLDO pin is
actively discharged when LDOSW is disabled"* — pull-down VLDOSWPD = 2 kΩ (PS
Tables 11–12). No register dance; +3V3_FDC_SW is driven to ground between wakes
rather than floating, which is the exact condition the old design had to
configure by hand.

Both buses use 4.7 kΩ pull-ups and the qualification firmware runs them at
100 kHz. Verify rise time after routing; low-state current comes from each
bus's respective supply, while idle-high current is leakage only.

### FDC1004 electrical — verified against SNOSCY5

| Param | Value | Consequence |
|---|---|---|
| Supply | **3.0 min / 3.3 nom / 3.6 max V** | boost at ±5% gives 3.135–3.465 V, and the LP/ULP +50 mV average offset peaks ~3.39 V — inside spec |
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

**A boost-ripple gotcha worth acting on.** PSRR is 13.6 fF/V. In Auto mode the
boost sits in LP/ULP at our load, where VOUT ripple is **70 mV_pp** (PS Table 10,
VOUTLP_RIPPLE — and note the LP/ULP average sits 50 mV above target, VOUTLP) —
that injects **0.95 fF** of error against a ±6 fF budget, roughly 16% of it,
before you have measured anything. Forcing High Power mode for the conversion
window cuts the ripple to the 2 MHz PWM regime's level, roughly a 10× improvement
on the nPM2100 boost converter.

HP costs 7.2 mA quiescent (PS Table 4, IQHP), but only for the conversion window:
20 ms × 8760 wakes ≈ **0.35 mAh/yr** against a ~18 mAh/yr budget (§7). **Force HP
over TWI for the measurement, then return to Auto immediately.** This is exactly
the kind of thing the enormous power slack in §7 is there to buy.

**The old rail-sag problem is gone.** A boost holds 3.3 V from VBAT 3.4 V down to
0.7 V (PS Table 4, VBATOVR), so the FDC1004's 3.0 V minimum is maintained for the
cell's entire useful discharge — on the old buck design the rail sagged below
3.0 V near cell-empty. What remains at end of life is pulse droop through the
cell's rising ESR: treat moisture readings as invalid when the PMIC reports a
VOUT droop event or low VBAT (§3) rather than reporting garbage.

### Load switch — verified against PS §6.2 / Table 12

| Param | Value | Consequence |
|---|---|---|
| Supply | LDOSW is fed from VINT internally | no external feed net; +3V3_FDC_SW comes straight off pin 12 |
| R_ON, High Power mode | 500 mΩ | At ~750 µA that is 0.4 mV of droop. Irrelevant |
| R_ON, Ultra-Low Power mode | 40 Ω | Only relevant in hibernate — we do not convert there |
| I_out max | 50 mA (HP) / 2 mA (ULP) | 60× headroom in HP mode |
| IQ, switch mode | 20 nA (ULP) / 50 µA (HP) | Only during the wake window |
| Default state | **OFF** | Safe: the FDC1004 is unpowered until firmware asks |
| Active discharge | built in, 2 kΩ | +3V3_FDC_SW collapses between wakes; no floating rail |
| OCP | enabled by default | configurable in `PRGOCP` |

**The LP/ULP average-offset note applies to +3V3_FDC_SW.** In load-switch mode LSOUT
passes VINT, and in LP/ULP the boost's average output sits at target + 50 mV
(VOUTLP, PS Table 10) with ±35 mV of ripple around it — so +3V3_FDC_SW peaks near
3.385 V at a 3.3 V target, inside the FDC1004's 3.6 V maximum with margin.

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
| 8 | VDD | Power | +3V3_FDC_SW |
| 9 | SCL | Input | FDC_SCL |
| 10 | SDA | I/O | FDC_SDA |

There is **no address pin**: FDC1004 uses fixed address 0x50 on its dedicated
bus. SHT40 and nPM2100 remain together on the main bus — see §8.

Supply current and voltage range are now verified — see the electrical table above.

### Ambient RH/T — SHT40-AD1F

Added primarily as a **compensation input**, not a feature. Verified against the
SHT4x datasheet v7.3; cost revision approved 2026-09-09.

| Param | Value |
|---|---|
| Part | **SHT40-AD1F** — typical ±1.8 %RH, **±0.2 °C**, integrated filter membrane |
| Supply | 1.08–3.6 V (keeps working after the FDC1004 has dropped out) |
| I_DD idle | **80 nA** typ, 1.0 µA max @ 25 °C |
| I_DD measuring | 320 µA typ, 500 µA max |
| Measurement time | 6.9 ms typ high-repeatability (1.3 ms low) |
| Power-up | 0.3 ms typ, 1 ms max |
| I²C address | **0x44** |
| Package | DFN-4 1.5×1.5×0.5 mm, 0.8 mm pitch |
| Footprint | `Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad` |

**Reference accuracy and compensation.** SHT40 is accepted as an ambient
temperature/humidity reference. It has the same 0x44 address, pin assignment,
measurement commands and conversion formulae as SHT45. The existing bring-up
firmware needs no protocol change. Typical ±0.2 °C and ±1.8 %RH values apply
under the datasheet's stated conditions; they are not full-range guarantees.

If ambient temperature is used for soil compensation, the earlier illustrative
20–60 fF/°C soil coefficient implies 4–12 fF uncertainty from ±0.2 °C, versus
2–6 fF for SHT45. That is a design estimate, not measured moisture accuracy.
Ambient temperature can differ from soil temperature; calibrate the assembled
probe over its actual conditions before using this compensation model.

The AD1F integrated membrane is retained. Sensirion's v7.3 datasheet describes
it as polyimide; older product pages describe PTFE. Procurement is locked to
the exact Sensirion SHT40-AD1F-R2 code, not an unfiltered AD1B or another brand.

**It must sit on the always-on +3V3 rail, not on gated +3V3_FDC_SW.** Table 6 rates
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

### Battery voltage and state of charge — nPM2100 ADC + host fuel gauge

The nPM2100 measures **VBAT, VOUT and die temperature** with an internal 8-bit
ADC (PS §7.1): VBAT to ±1% typ at 25 °C over 0.7–3.2 V, die temp ±8 °C over
−10…60 °C, conversion in 100 µs. This still deletes the resistor divider, its
standing drain, the abs-max hazard and all the SAADC work — there is no external
divider in the production design.

On top of the measurements, Nordic's **nRF Fuel Gauge** host library (nrfxlib)
computes state of charge from VBAT + die temperature against a battery model —
and the **default LiMnO₂ model is the CR2032** (nan_048 §3). What BTHome reports
as battery % is therefore a real SoC estimate, not a voltage guess, which matters
on a LiMnO₂ discharge curve that is nearly flat from 100% to ~20%.

Firmware requirements from nan_048:

- **Initialize once per battery insertion, under load.** Primary cells' voltage
  recovers at rest and inflates the initial estimate; initialize while battery
  current exceeds 2 mA — or force the boost to HP for ~500 ms before the first
  reading (nan_048 §4.2).
- **Persist the fuel-gauge state across sleeps.** The state is a few hundred
  bytes; reinitializing every wake degrades accuracy (nan_048 §4.1). With the
  System OFF architecture the state can live in retained RAM; verify retention
  behaviour on nRF54L15, else persist to RRAM/flash (and check write endurance
  against ~8760 writes/yr).
- **CR-series reporting granularity is coarse.** Recommended step sizes are 25%
  through the mid-range (±25% error band) and 5% below 25% (nan_048 Table 2) —
  LiMnO₂ flatness is physics, not a library limitation. BTHome battery % will
  move in coarse steps above 25% and that is correct behaviour.
- Cost is negligible: < 4 µC per iteration (nan_048 Table 3), once per wake.

---

## 6. Module pin assignment

Verified against Ezurio's current BL54L15 pin table. All firmware GPIO numbers
are preserved; module pad numbers replace the bare-QFN numbers.

| Signal | Module pad | SoC function |
|---|---|---|
| SCL | 35 | P1.11 / dedicated clock |
| SDA (PMIC/SHT) | 28 | P1.10 |
| FDC_SDA | 22 | P1.05 |
| FDC_SCL | 23 | P1.04 |
| PMIC interrupt | 17 | P0.00 / wake-capable |
| SWO | 4 | P2.07 |
| SWDIO / SWDCLK / nRESET | 5 / 6 / 7 | Dedicated debug/reset |
| XL1 / XL2 | 25 / 24 | P1.00 / P1.01 reserved for X1 |
| VDD / GND | 26 / 1,16,27,39 | +3V3 / GND |

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

SDA and SCL use adjacent SoC functions inside the module. The datasheet
requires the data signal to "use pins close to the clock pin" so the internal
path delays match, and asks for short traces of identical length on the PCB.

P1.03 was avoided as a clock pin because it is NFC2 and **NFC is enabled from
reset** — using it as GPIO means disabling NFC in the PADCONFIG register first.

SWD header: SWDIO, SWDCLK, RESET, 3V3, GND. RESET keeps the R1/C13 filter from §2.

**The nPM2100's PG/RESET output joins the RESET net** (§3): open-drain with an
internal pull-up to VINT, wired-OR compatible with R1, C13 and the SWD
connector. No nRF pin moves — the change is that /SWD_RST now has a second
driver, so the watchdog can reset the SoC (or power-cycle it) independently of
the debug connector. The PMIC event interrupt is now nPM2100 GPIO0 (pin 5) on
the same /PMIC_INT net and pin as before.

---

## 7. Power budget

The estimates below predate the module migration. Re-measure the complete
BL54L15 board, including HP-mode radio windows; they are not validated module
battery-life figures.

### Result

**Cell: CR2032 LiMnO₂, 225 mAh nominal** (any major brand — Panasonic, Murata,
Duracell; the fuel gauge's default LiMnO₂ model is the CR2032, nan_048 §3).
User-replaceable; battery-out is the off switch. The production holder is Lian Xin
`CR2032-BS-6` (LCSC C22363833), placed in Zone B away from the sense escape and RF corridor.

| Item | Current | mAh/yr | Scales with capacity? |
|---|---|---|---|
| CR2032 self-discharge | ~1%/yr | 2.3 | **yes** |
| nRF54L15 System OFF + GRTC/LFXO | ~0.9 µA **[assumed]** | 7.9 | no |
| nPM2100 quiescent, boost ULP | 0.3 µA (PS Table 4) | 2.6 | no |
| SHT40 idle (always powered) | 80 nA | 0.7 | no |
| Boost inefficiency on the above | ~10% | ~1.1 | no |
| Hourly wake cycles (300 ms @ ~4 mA battery-side) | — | ~3.5 | no |
| Fuel gauge iterations | < 4 µC each | ~0 | no |
| **Total** | | **≈ 18 mAh/yr** | |

Runtime = 0.95 × 225 / 18 ≈ **11.9 years — past the CR2032's own ~10-year shelf
life.** The cell's chemistry, not the electronics, is the life limit. That was
the entire point of the architecture change: the old rechargeable-cell budget was 74%
self-discharge at 2%/month; LiMnO₂ self-discharges at ~1%/*year*, a 24×
improvement no layout decision could buy.

Every electronics term is now irrelevant to the headline number. Halving the
sleep current buys ~1.3 years of a figure the shelf life caps anyway; doubling
the wake cycle costs ~0.2. **Do not spend board area or firmware complexity
chasing microamps on this design.** The only two numbers worth measuring at
bring-up are the actual sleep current (assumption 1) and the end-of-life pulse
behaviour (§3).

### Assumptions — check these

1. **nRF54L15 System OFF ≈ 0.9 µA with GRTC/LFXO running.** The old budget's
   combined PMIC + nRF System OFF estimate split as PMIC + ~700 nA SoC, so this
   is consistent with what was budgeted before, but it is now the
   single largest electronics term. Measure it — PPK2 on the EK+DK wiring, the
   same session that validates the §5 gating sequence.
2. **Boost efficiency ~90% at the µA-level sleep load.** nwp_058 Table 5
   measures 91.9% at 100 µA for the selected inductor; at ~1 µA it will be lower
   (nwp_058 Figure 2 shows the curve). Budgeted generously; the term is small
   either way.
3. **Wake cycle 300 ms at ~4 mA battery-side** — the old 3 mA at VDD plus boost
   overhead. A composite estimate, not measured; at ~20% of budget even a 5×
   error changes the answer by less than a year.
4. **8760 wakes/yr, one fuel-gauge iteration per wake** (nan_048 Table 3).
5. **CR2032 self-discharge ~1%/yr, shelf life ~10 yr** — the standard LiMnO₂
   figure at room temperature. **[assumed — get the figures from the brand you
   actually buy; it is the only cell-dependent term left and it is small]**
6. **20–25 °C ambient.** A device on a hot windowsill ages the cell faster than
   any electronics term above.
7. **The 225 mAh rating assumes a gentle load profile.** Our peak (radio TX
   through the boost) is ~5–8 mA for milliseconds — inside CR2032 pulse ratings
   with CVBAT fitted, but usable capacity shrinks at the ESR knee. The +100 µF
   VBAT option (§3) buys margin if the bench numbers disagree.

---

## 8. Open items

- I²C addresses all confirmed distinct: **FDC1004 0x50** (SNOSCY5 §6.5.1),
  **SHT40-AD1F 0x44**, **nPM2100 0x74** (PS §7.6). One bus, no split needed.
- **Fuel gauge library availability**: nrfxlib nRF Fuel Gauge for nRF54L15 on our
  NCS v3.2.2 — confirm, and decide the state-persistence route (retained RAM
  through System OFF vs RRAM/flash per wake, nan_048 §4.1; check write endurance
  against ~8760 writes/yr if RRAM).
- **Bench: real sleep current** — PPK2 on the nPM2100 EK wired to the DK on our
  pins, validating both §7 assumption 1 and the §5 gating sequence in one session.
- **Bench: EOL CR2032 pulse behaviour** — with and without the +100 µF VBAT
  option (§3), against the droop detector.
- **Zephyr driver coverage** — mfd/regulator/gpio/watchdog/vbat drivers exist in
  mainline Zephyr and the nPM2100 EK has an in-tree shield overlay; verify the
  fuel-gauge sample runs against NCS v3.2.2's Zephyr revision.
- Cell holder and polarity handling are locked to Lian Xin `CR2032-BS-6` (C22363833) and the
  placement described in §3; Q1 reverse protection now requires prototype validation.
- Validate BL54L15 supply ripple, oscillator trim and closed-enclosure radiated
  performance. The fixed battery geometry does not meet every preferred metal
  clearance; see docs/bl54l15/README.md.

---

## 9. Why the production power architecture is primary-cell

Recorded so the decision is not relitigated later.

The product uses a single user-replaceable watch battery. A rechargeable-cell
charger topology cannot accept a CR2032 or boost its 2.0–3.0 V discharge curve
to a valid 3.3 V rail, so the production design uses the nPM2100 instead.

The nPM2100 is built for precisely this case: a boost front end regulating
3.3 V from 0.7–3.4 V, a primary-cell fuel gauge whose default model is the
CR2032, ship/hibernate states at 35–320 nA, and a load switch to gate the sensor
front end. The FDC1004 gating topology, always-on-rail I²C pull-up placement,
deadlock analysis (§5), and nRF54L15 pin assignment (§6) are all part of the
production design. USB-C, solar, rechargeable-pack protection, charge LEDs, and
VBUS current-limit firmware are absent.

The deleted charging architecture is not dead work — it is board 2's starting
point. A pump controller that is "battery or plugged in" is exactly the
USB-C-charged rechargeable device the old power tree described.

---

## Sources

- [Ezurio BL54L10/BL54L15 datasheet](https://www.ezurio.com/documentation/datasheet-bl54l10-and-bl54l15-series), accessed 2026-09-04 — current module pinout and host integration.
- [Nordic LFXO devicetree guidance](https://docs.nordicsemi.com/r/bundle/ngl_001/page/gl/ngl_001/lfxo_devicetree.html) — capacitance parameter semantics.

- [nPM2100 Product Specification v1.0](https://www.nordicsemi.com/Products/nPM2100) (local: `doc/datasheets/nPM2100_Datasheet_v1.0.pdf`) — Tables 4–7, 10–12, 15–18, 20, 22, 25–27, 38; §6.1–6.2, §7.1–7.6, §9.3
- [nPM2100 Hardware Design Guidelines, nwp_058, March 2025](https://www.nordicsemi.com/Products/nPM2100/Documentation) (local: `doc/datasheets/nPM2100_HW_Design_Guidelines_nwp_058.pdf`) — inductor and capacitor selection, CR2032 reservoir-capacitor test
- [Using the nPM2100 Fuel Gauge, nan_048, July 2025](https://www.nordicsemi.com/Products/nPM2100/Documentation) (local: `doc/datasheets/nan_048.pdf`)
- [nPM2100 EK Hardware — User Guide v0.9.0](https://www.nordicsemi.com/Products/nPM2100/Documentation) (local: `doc/datasheets/nPM2100_EK_User_Guide.pdf`) — EK wiring, VSET/LDOSW/reservoir jumpers
- [Reverse battery protection for the nPM2100 PMIC, ngl_002, March 2026](https://www.nordicsemi.com/Products/nPM2100/Documentation) (local: `doc/datasheets/nPM2100_Reverse_Battery_ngl_002.pdf`)
- [Lian Xin CR2032-BS-6 drawing](doc/datasheets/lianxin-cr2032-bs6/CR2032-BS-6.pdf) — selected holder land pattern and assembly dimensions; [source and model notes](lib/footprint-sources/CR2032-BS-6.md)
- [Murata DFE201210U-2R2M=P2](https://www.murata.com/en-global/products/productdetail.aspx?partno=DFE201210U-2R2M%23) — electrical and mechanical selection
- [Molex 2069940100 product specification](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/206/206994/2069940100-PS.pdf) — retired external antenna (historical reference)
- [nRF54L15 reference circuitry, circuit configuration 1 for QFN48 (QFAA)](https://docs.nordicsemi.com/r/bundle/ps_nrf54l15/page/chapters/ref_circuitry.html-concept_refcircuit_config_1) — Tables 1 and 2, grounding notes
- [nRF54L15/L10/L05 datasheet v1.0](https://www.mouser.lt/datasheet/3/926/1/nRF54L15_nRF54L10_nRF54L05_Datasheet_v1.0.pdf) — System OFF current figures
- Zephyr nPM2100 drivers and nPM2100 EK shield overlay (zephyrproject-rtos/zephyr: `drivers/mfd/mfd_npm2100.c`, `drivers/regulator/regulator_npm2100.c`, `boards/shields/npm2100_ek/`) — I²C address 0x74, driver availability; Nordic's bare-metal reference (`nordicsemi/npm2100-bm`) for register semantics

## Test access

TP4–TP17 add main-rail/FDC/VINT voltage and ground pairs, protected/raw battery, I²C, PMIC interrupt, filtered NRESET and two timing-marker GPIOs. **TP16 = P1.09 (U1.29); TP17 = P1.08 (U1.30).** See the [test-point map and verification](docs/testpoints-2026-09-07/README.md).

## Cost revision — 2026-09-09

Q1 uses DMG2305UX-13 / C144153, the same Diodes device with a different reel
size. C3 uses CL10A106MA8NRNC / C96446 in the existing 0603 footprint.
Samsung's typical DC-bias data gives 6.60 µF at 3.3 V versus 6.85 µF for the
previous C3. X5R is rated −55 to +85 °C, consistent with the other retained
X5R capacitors; this is not a board temperature qualification. Total nominal
VOUT capacitance remains 12.3 µF. Existing module ripple, transient and total
effective output-capacitance qualification remains required.

C26 retains GRM155Z71A105KE01D. The screened Basic 1 µF alternative loses
about 42% at 3.3 V and has not been qualified against the FDC rail requirements.
R22/R23/R36/R37 now share the value `4.7k 1%` and C25900 so the BOM groups
all four without changing their two separate supply nets.
See [part evidence and checks](docs/cost-reduction-2026-09-09/README.md).
