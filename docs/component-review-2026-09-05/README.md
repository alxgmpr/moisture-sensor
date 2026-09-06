# I²C and capacitor review — 2026-09-05

Reviewed the current nRF Moisture Sensor schematic using a freshly exported
[netlist](netlist.xml), and checked PCB pad net/function assignments in
[pad-audit.json](pad-audit.json). This is a design review and analytical check;
no assembled-board measurement or converter transistor-level simulation was run.

## I²C pin assignment is correct

| Signal | Module U1 pad | nRF54L15 GPIO | Internal QFN pad | Other bus pins |
|---|---|---|---|---|
| SCL | 35 | P1.11, dedicated clock | 39 | U2.7, U3.9, U4.2, R23.2 |
| SDA | 28 | P1.10 | 38 | U2.6, U3.10, U4.1, R22.2 |

The [Ezurio pin table](https://www.ezurio.com/documentation/datasheet-bl54l10-and-bl54l15-series)
confirms this mapping. The two signals are adjacent on the silicon package;
the module redistributes them to lands 5.25 mm apart. Module pad numbering does
not define a mandatory I²C pair. No pin swap is needed.

Nordic nRF54L15 Product Specification v1.0 §8.8.3–8.8.5 (pp.276–278)
requires a peripheral-compatible port and a clock-capable clock pin. §8.23.10
(p.659) assigns TWIM20/21/22 to P1 and TWIM30 to P0. **TWIM22 with SCL=P1.11,
SDA=P1.10 satisfies these constraints.** Use separate PSEL settings for SCL and
SDA; do not use TWIM30 for this pair. Local source:
[Product Specification](../../doc/datasheets/nRF54L15.pdf).

The existing [pin test overlay](../../firmware/pin-assignment/boards/nrf54l15dk_nrf54l15_cpuapp.overlay)
sets exactly this pair on `i2c22`. [Bench records](../../firmware/README.md)
report 20/20 successful DK transactions for this configuration. Those are
historical DK results, not a test of the present module PCB. The BTHome app still
targets the DK; the [module firmware port requirements](../../firmware/BL54L15-port.md)
remain applicable. Peripheral sharing (for example TWIM20/UARTE20) must also
be considered when creating the actual board target.

R22/R23 are 4.7 kΩ. Using the first-order I²C relation
`t_r = 0.8473 R C`, 400 kHz's 300 ns rise-time limit allows about **75 pF** per
line (74.6 pF at resistor +1%); 100 kHz's 1 µs allows about **251 pF**.
These are analytical budgets, not extracted bus capacitance. Verify rise times
at the farthest device with all devices fitted. Do not add capacitors to SDA or
SCL. Power sequencing must also prevent the always-on pull-ups from back-powering
the switched-off FDC1004.

## Current capacitor inventory

This table comes from the current schematic, not the older BOM prose. All power
capacitors below return to GND.

| Ref | Actual schematic selection | Rail / function | Assessment |
|---|---|---|---|
| C3 | Samsung CL10X106MO8NRNC; 10 µF 16 V X6S, 0603, ±20% | +3V3, module input | Correct nominal host reservoir; include in total VOUT effective capacitance. |
| C13 | FH 0402CG3R9C500NT; 3.9 pF C0G, 0402 | NRESET RF filter | Not supply bypass or a millisecond reset delay. No capacitance increase indicated. |
| C21 | Samsung CL05A106MQ5NUNC; 10 µF 6.3 V X5R, 0402, ±20% | VBAT | **Marginal at fresh-cell DC bias; not qualified**, see below. |
| C22 | FH 0402B102K500NT; 1 nF 50 V X7R, 0402 | VBAT HF bypass | Within Nordic's 1–100 nF supplementary range. |
| C23 | Murata GRM155R60J226ME11D; 22 µF 6.3 V X5R, 0402, ±20% | VINT boost reservoir | Nominally reasonable; exact biased minimum still unresolved. |
| C24 | FH 0402B102K500NT; 1 nF 50 V X7R, 0402 | VINT HF bypass | Within Nordic's supplementary range. |
| C25 | Samsung CL05A225MQ5NSNC; 2.2 µF 6.3 V X5R, 0402, ±20% | +3V3, converter output | Matches recommended nominal value; check effective local capacitance and total load. |
| C26 | Murata GRM155Z71A105KE01D; 1 µF 10 V X7R, 0402, ±10% | +3V3_FDC_SW | Correct nominal value/dielectric for TI recommendation. |
| C27 | Samsung CL05B104KO5NNNC; 100 nF 16 V X7R, 0402, ±10% | +3V3, SHT45 | Appropriate local HF bypass; not an energy reservoir for heater pulses. |
| C28 | Samsung CL05B104KO5NNNC; 100 nF 16 V X7R, 0402, ±10% | +3V3_FDC_SW | Correct TI bypass paired with C26; must be closest to U3 VDD. |

At review time BOM.md still calls C26–C28 unresolved and lists obsolete 0201
parts for C22/C24/C27/C28. **Synchronize published BOM/readme prose with these
actual source selections.** The electrical fields already contain order codes.
BOM.md has now been regenerated from KiCad source fields (see the 2026-09-05 product CSV).
No part substitutions were made by this review.

## Power findings

**1. C21 lacks adequate demonstrated margin.** Nordic requires at least 3.5 µF
effective capacitance on VBAT. The exact-part
[Samsung characteristic sheet](https://media.digikey.com/pdf/Data%20Sheets/Samsung%20PDFs/CL05A106MQ5NUNC_Char.pdf)
shows approximately 60% loss around 3.2–3.3 V in its DC-bias graph. A screening
estimate gives `10 µF × 0.40 × 0.80 ≈ 3.2 µF`, below 3.5 µF. The separate
biased-temperature graph is somewhat less severe; this typical-only sheet does
not establish a guaranteed worst case. Confirm the current manufacturer model
and minimum capacitance at fresh-cell voltage, temperature and aging; otherwise
revise the input reservoir selection. A 1 nF bypass does not close a microfarad
shortfall. [Locally inspected plot](c21-characteristics.png).

**2. C23 cannot be approved from “22 µF” alone.** VINT also requires at least
3.5 µF effective. At −20% tolerance, C23 needs at least 19.9% of nominal
capacitance remaining before additional temperature/aging allowances. Obtain
its exact bias curve at actual VINT voltage (including operating modes), not a
curve from a similarly named Murata part. The schematic's part is not the exact
22 µF example printed in Nordic's application note. VINT is the preferred node
for additional output energy storage if analysis shows more is needed.

**3. Main +3V3 has an unresolved maximum-capacitance budget.** Nordic specifies
0.7–15 µF effective capacitance on VOUT. Direct external loading is
`C3 + C25 + C27 = 12.3 µF` nominal. Using listed production tolerances alone
and zero bias reduction gives **14.75 µF**; this excludes module-internal
input capacitance, temperature increases, parasitics and any attached debugger.
The FDC load-switch branch is supplied from **VINT**, explicitly stated in
nPM2100 §6.2 (p.42); C26/C28 must **not** be added directly to the VOUT
15 µF budget. Their switching load can disturb the common boost/VINT source,
so test that transient independently. The direct-VOUT arithmetic is a screening
bound, not proof of failure: real MLCC bias loss affects the result. Quantify the
module's input capacitance and full operating temperature range.
Blindly adding a large capacitor to +3V3 could violate the converter limit.

**4. Radio supply ripple needs hardware qualification.** Ezurio specifies at
most 10 mV supply noise/ripple for undisturbed radio operation and calls for
10 µF at the host supply. Nordic's nPM2100 LP/ULP typical output ripple is
70 mVpp. Hold HP through radio activity and settling, then measure at module
pad26; HP is a mitigation, not a guaranteed compliance result. This is a larger
open power issue than nominal microfarads alone.

**5. FDC bypass values match TI.** The
[TI FDC1004 datasheet](https://www.ti.com/lit/ds/symlink/fdc1004.pdf),
§7.5 in the local revision, recommends 0.1 µF and 1 µF X7R, with the smaller
capacitor nearest VDD. C28/C26 satisfy the value/dielectric requirement.
The PMIC output is used as a load switch, so the LDO-specific output-capacitor
minimum does not impose an additional capacitor here. Preserve local bypass
placement and test switched-rail start-up/back-power behavior.

**6. The SHT45 heater is a separate load case.** The local
[SHT4x v7.3 datasheet](../../doc/datasheets/sensirion-sht45/HT_DS_Datasheet_SHT4x_V7.3.pdf),
Table 4, lists highest-heater current as 60 mA typical and **100 mA maximum**;
normal measurement is at most 500 µA. Use the table's 100 mA maximum for power
budgeting, rather than the approximate 75 mA sentence later in the document.
C27 is ordinary local decoupling. At 100 mA, 100 nF supports a 10 mV drop for
only 10 ns (`dt=C·dV/I`); it cannot supply a 0.1 s heater cycle. If heater use
is intended, qualify converter and depleted/cold CR2032 behavior independently
and avoid simultaneous radio bursts. No need to enlarge C27 simply to match
the heater current.

The fitted X1 uses the SoC's internal load banks, so adding arbitrary discrete
crystal load capacitors is inappropriate. Follow the existing port calculation
and trim/start-up verification; its initial 12 pF internal-per-leg estimate is
not a measured calibration.

## Simulation and bench tests to close the findings

1. Sweep exact capacitor bias/temperature models, tolerance and aging across
   battery voltage and PMIC modes. Confirm VBAT/VINT minima, local VOUT minimum,
   and aggregate VOUT maximum. Check FDC switching transients separately on the
   VINT-derived branch. Use the actual assembled module's
   input capacitance. Typical curves provide engineering estimates, not lot limits.
2. Model CR2032 open-circuit voltage and series impedance versus temperature and
   depletion, converter response, actual routing resistance and load pulses.
   Sweep module TX/RX, FDC turn-on and 10/55/100 mA heater maxima. A behavioral
   load-step simulation can bound droop, but cannot prove converter loop stability
   or RF noise without a validated converter/module model.
3. On prototypes, use a short ground spring at module pad26 and U3/U4 supplies;
   capture startup, HP/LP transitions, radio bursts and FDC switching. Check
   radio supply noise against 10 mV and FDC supply staying within 3.0–3.6 V.
4. Verify I²C rise times, transactions and idle current with the FDC rail off/on;
   repeat at minimum battery voltage and relevant temperatures. Compare radio
   performance with the PMIC forced HP versus automatic mode.

Nordic sources for the capacitance/mode findings:
[nPM2100 Datasheet v1.0](../../doc/datasheets/nPM2100_Datasheet_v1.0.pdf),
Table 10 (pp.17–18), and
[Hardware Design Guidelines nwp_058](../../doc/datasheets/nPM2100_HW_Design_Guidelines_nwp_058.pdf),
§3.2–3.4 (pp.9–10). All manufacturer documents were read locally or retrieved
on 2026-09-05. Extracted full-document text was temporary and is not retained.
