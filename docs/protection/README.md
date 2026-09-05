# Protection implementation — 2026-09-04

Implemented in the maintained schematic and PCB at Alex's request. This is an
unqualified prototype design, not a fabrication release or IEC immunity claim.
The baseline already had 15 missing module connections; this revision retains
15 missing connections, with SWD endpoints now terminating at series resistors.
No unrelated module fanout was routed. No parts were ordered.

## Implemented circuits

| References | Part / function | Connections |
|---|---|---|
| Q1 | Diodes DMG2305UX-7, SOT-23 PMOS | 3/drain = VBAT_RAW, 2/source = protected VBAT, 1/gate = GND |
| D1 | TI TPD1E1B04DPYR, bidirectional ESD suppressor | Raw battery positive to ground; F.Cu beside positive contact |
| D2 | TI TPD1E1B04DPYR | Protected VBAT to ground |
| D3 | TI TPD1E1B04DPYR | J4 supply-reference / +3V3 to ground |
| D4–D7 | TI TPD1E01B04DPYR | External SWDIO, SWDCLK, SWO, reset to ground |
| R32–R35 | Yageo RC0402FR-07100RL, 100 ohm 1% | Between programming contacts/clamps and internal signal nets |
| D8–D9 | TI TPD1E01B04DPYR | SENSE1 / SENSE2 electrode side to ground |
| R30–R31 | Yageo RC0402FR-075K1L, 5.1 kohm 1% | Electrode/clamp side to FDC CIN1 / CIN2 |
| D10 | TI TPD1E01B04DPYR | Driven shield to ground; no large series impedance in shield drive |

C21/C22 remain on protected VBAT at the PMIC. Q1 body diode orientation starts
normal battery operation and blocks reversed polarity after the channel turns
off. A single PMOS does not guarantee reverse-current blocking from an externally
powered system into the primary cell. J4 is a target voltage reference, not an
approved external supply input; use the cell to power the board during debugging.

The selected MOSFET specifies 200 mohm maximum at VGS = -1.8 V, 25 C, and
100 nA maximum gate leakage at ±8 V, 25 C. At 150 mA the former corresponds to
30 mV drop; this is a sizing calculation, not measured converter efficiency.
Hot leakage, cold start and end-of-life pulse performance need measurement.

The signal suppressor has 0.18 pF typical capacitance and 10 nA maximum leakage
at ±2.5 V. These values are not guarantees at every operating voltage and
temperature. TPD1E1B04 trades higher capacitance for lower dynamic resistance on
power nets. D1 is bidirectional so reversed battery insertion does not create
the forward-biased shunt path of a unidirectional TVS on the raw input.

The 5.1 kohm input resistors limit residual clamp current; they are an initial
prototype value. For 100 pF, RC is 0.51 us. That estimate is not a proof of
settling accuracy for the FDC's switched-capacitor input. Validate full-scale
range, noise, drift, and coated dry/wet calibration. Do not interpret CAPDAC
headroom as proof that voltage-dependent TVS capacitance is harmless.

## PCB and assembly

- Q1 sits below the battery's removal-tool courtyard. D1 is now on F.Cu at
  (61.2, 86.0) mm, beside the positive contact; all protection parts use front PCBA.
- BT1's stepped courtyard follows the terminal/plastic/round-body envelopes with
  0.25 mm body clearance and retains the 10.5 × 4 mm removal-tool extension.
  Only unused bounding-box corners were released; the holder/pads were not moved.
- The TI DPY0002A footprint follows the datasheet land pattern: two 0.3 × 0.5 mm
  pads on 0.7 mm centres. All ten diodes now use TI's actual DPY0002A STEP model
  (1.0 × 0.6 × 0.45 mm), with molded body and two metal terminals. The previous
  D1 library mismatch is resolved. See [model provenance](diode-front/model.json).
- Each clamp has its own nearby ground via. Probe ground vias return to In1;
  driven-shield copper and the long probe routes remain. TP1 and TP2 moved from
  y=113 to y=115.5 mm to clear the series resistors; these are test contacts,
  not the electrode shapes.
- `CIN1_PROTECTED` and `CIN2_PROTECTED` retain the SENSE class. Raw battery and
  external debug nets have explicit Power/Control classes.
- Two small ESD_SENSE rule areas permit 0.127 mm clearance at the intentional
  ground-referenced clamp terminals and their short fanout. The TVS land gap is
  0.4 mm, incompatible with the general 1 mm sense-to-ground rule. Long sense
  routes retain that rule. Physical shorts, holes and other checks remain enabled.
- Dense new reference designators are on assembly/fabrication layers. Exact
  purchasing MPNs are in schematic/PCB fields, BOM.md and parts.json. Distributor
  stock codes and assembly availability are not verified.

## Not implemented

No PTC/fuse and no independent sustained-overvoltage disconnect. The nPM2100's
internal BOOST/LDOSW protection remains; it cannot interrupt every battery-side
short. A PTC needs trip-time verification with a real CR2032 over temperature,
and added resistance must be checked against startup/pulse droop. An eFuse or
OVP disconnect needs a suitable low-voltage and leakage budget before selection.

TVS standoff voltage is not its clamping voltage. These clamps can exceed the
protected ICs' DC absolute maximum during a pulse; system survival depends on
waveform, layout, source impedance and internal pin robustness. In particular,
D10/shield and the power inputs require bench qualification. Do not apply a
rechargeable 4.2 V cell, a 5 V programmer supply, or sustained overvoltage.
The nPM2100's supported input maximum remains 3.4 V.

## Verification and required prototype tests

ERC: zero errors, 11 pre-existing library warnings. PCB: zero physical errors,
zero schematic parity issues, 15 pre-existing missing module connections.
16 PCB warnings remain from existing library/silk/route anchors; no diode or
holder footprint mismatch remains.
All 38 repository tests pass. No rules were disabled and no violations excluded.
The checked netlist fingerprint includes the intentional protection changes.

Before fabrication, finish the original module routing and reconcile warnings.
Before calling the protection qualified, measure normal/reversed insertion,
leakage over temperature, fresh/aged-cell startup and radio bursts, programming
at the intended SWD clock, powered/off-state ESD on each accessible connection,
and sensor noise/calibration before and after ESD. Inspect the final enclosure and coating mask. These bench tests have not been performed.

## Sources and review artifacts

- [Nordic reverse-battery guideline](../../doc/datasheets/nPM2100_Reverse_Battery_ngl_002.pdf)
- [Nordic nPM2100 datasheet](../../doc/datasheets/nPM2100_Datasheet_v1.0.pdf)
- [DMG2305UX manufacturer datasheet](https://www.diodes.com/datasheet/download/DMG2305UX.pdf)
- [TPD1E01B04 manufacturer datasheet](https://www.ti.com/lit/ds/symlink/tpd1e01b04.pdf)
- [TPD1E1B04 manufacturer datasheet](https://www.ti.com/lit/ds/symlink/tpd1e1b04.pdf)
- [Protection schematic](schematic.png), [final ERC](final-erc.json),
  [final DRC](final-drc.json), [tests](tests.txt), [netlist](netlist.xml)

Front-PCBA revision visuals: [holder courtyard and D1](diode-front/courtyard.png),
[TI model on an isolated preview board](diode-front/model-preview.png), and
[placement export confirming D1 on top](diode-front/positions.csv).
