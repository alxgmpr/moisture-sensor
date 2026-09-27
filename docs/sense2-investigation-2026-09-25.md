# SENSE2 low soil response — 25 September 2026

Status: the low soil response is confirmed by the supplied paired experiment. A subsequent marked hand-grip/release experiment on Soil-531E demonstrates a strong, sustained and reversible SENSE2 response. The soil-specific cause remains unresolved; no firmware defect has been identified. Neither calibration nor firmware has been changed during this investigation. Both pads are soil-sensing electrodes. The user confirms both were completely covered and that the devices use the current PCB revision; the old air-reference label is obsolete.

## Evidence and interpretation

| Device / condition | SENSE1 fF | SENSE2 fF | Interpretation |
|---|---:|---:|---|
| Soil 1, buried (user's prior live measurement) | ~3550 | ~2095 | 29.80% / 0% under stored endpoints |
| Soil 1, lifted, settled (prior measurement) | ~2220 | ~2076 | Soil-minus-air difference ~1330 / ~19 fF |
| Soil-531E, buried (user's prior measurement) | ~3701 | ~2226 | 34.83% / 0% |

The SENSE2 change in the paired Soil 1 observation is only about 1.43% of SENSE1's change. Its reinsertion spikes establish a changing measured input, **not** continuity through R31 to the whole electrode, adequate steady-state sensitivity, or a wet calibration endpoint. An electrically isolated input can still respond through stray coupling.

The repository README identifies these endpoints as provisional water-submersion calibration, not validated soil endpoints; the originating raw water series and its exact fixture/device were not re-established in this session. That history does not prove current SENSE2 health.

The user reports Soil-531E's active image was confirmed as 0.2.28 after OTA; Soil 1 remains 0.2.27. The older `soil1-dual-pad-diagnosis-2026-09-24.md` predates that OTA and its statement that 0.2.28 was not uploaded is superseded by the user's update.

## Complete path comparison

Measurements below were extracted from the current native board's **filled polygons**, schematic XML netlist, and saved fabrication source. Native copper and protection-schematic renders were inspected. Evidence is in `output/sense2-investigation-2026-09-25/`.

| Stage | SENSE1 | SENSE2 |
|---|---|---|
| Electrode position, board coordinates | x=69–85, y=159–189 mm; lower/tip electrode | x=69–85, y=122–152 mm; upper electrode |
| Nominal size | 16 × 30 mm | 16 × 30 mm |
| Filled area, each layer | 479.989897 mm² | 479.989897 mm² |
| Copper layers | F.Cu, In1.Cu, In2.Cu, B.Cu | Same |
| Through-via stitching | 18 vias | 18 vias |
| Ground/SHLD copper overlapping electrode rectangles | None on any copper layer | None on any copper layer |
| Electrode feed | F.Cu, 0.25 mm; ~48.995 mm total segment length | F.Cu, 0.25 mm; ~10.612 mm total segment length |
| Test point | TP1 | TP2 |
| Series resistor | R30 pad 1 → pad 2 | R31 pad 1 → pad 2 |
| Current schematic / PCB value | 4.7 kΩ, 1% | 4.7 kΩ, 1% |
| Protected net | /CIN1_PROTECTED | /CIN2_PROTECTED |
| Shunt protection | D8 pin 1 to signal, pin 2 to GND | D9 pin 1 to signal, pin 2 to GND |
| Protection device | TPD1E01B04DPYR | Same |
| FDC1004 U3 input | Pin 2, CIN1 | Pin 3, CIN2 |
| Software array index | 0 | 1 |
| Measurement slot | MEAS1, register 0x08 | MEAS1, register 0x08, reconfigured after CIN1 |
| Config at CAPDAC=0 | 0x1000 | 0x3000 |
| Stored dry/wet endpoints (user's confirmed settings) | 2655 / 5658 fF | 2618 / 5571 fF |
| Output object | First BTHome 0x14 | Second BTHome 0x14 |

Both protected input routes are on F.Cu with short 0.25 mm signal tracks and 0.3 mm diode branches. The schematic and PCB assign the correct pins; there is no net swap, grounded SENSE2 electrode, missing inner/back electrode, or deliberate reference subtraction in the inspected design. Native DRC found zero unconnected items and no sensing-net short/clearance violation. It did find **three unrelated keepout errors and 55 warnings**, so this is not a claim that the whole board passes DRC. No layout repair was attempted.

The September 9 fabrication source has identical electrode polygons, feed segments and 18-via patterns. Its BOM/source specify **5.1 kΩ for both R30 and R31**, whereas the current design specifies 4.7 kΩ for both. This discrepancy does not create a channel asymmetry, but physical resistor values must be checked before modeling input settling. Old documentation describing four stitching vias or a protected 5.1 kΩ current BOM is not current geometry evidence.

The common /SHLD net connects U3 pins 1 and 6, TP3, D10 (to ground), and the guard copper on all layers. The active rectangles have same-net copper behind them, not shield backing. The upper electrode has about 14.9 mm of guard region before its top; the lower electrode is close to the tip. Together with the different feed lengths and proximity to the grounded electronics, that gives different field/return geometries despite equal electrode area. This is a confirmed geometric difference, **not a demonstrated explanation for the approximately 70:1 response ratio**. Buried copper copies do not multiply exposed sensing area by four; the outer faces principally couple to soil.

## Firmware and transport audit

`carrier_start()` shuts down the sensor rail, establishes the regulator's HP mode and 3.3 V output, enables the FDC switched rail, and waits 5 ms. Both channels are then acquired consecutively before sensor power is removed. Measure-now uses the same startup and acquisition path.

The FDC uses address 0x50 on its dedicated I²C bus; manufacturer/device IDs are checked. `capacitance()` writes `0x08 = (channel << 13) | 0x1000 | (CAPDAC << 5)`. CHA=0 selects CIN1, CHA=1 selects CIN2; CHB=4 selects CAPDAC. It writes `0x0c = 0x0480`: 100 samples/s, MEAS1 enabled, repeat disabled. It waits for DONE1 (bit 3), bounded at 30 one-ms waits. It reads registers 0x00 **then** 0x01. Reusing MEAS1 for both input pins is valid: input channel and result-slot number are different concepts. Reading 0x02/0x03 for SENSE2 without configuring/enabling MEAS2 would be incorrect.

Both result registers are consumed, which clears DONE1 per TI; the source therefore does not leave a stale completion bit deliberately unread. The 24-bit value is assembled as `(MSB << 8) | (LSB >> 8)`, sign-extended, and converted to fF as `raw * 1000 / 524288 + CAPDAC * 3125`. CAPDAC starts at zero independently for each channel, rises when residual exceeds 13 pF, and errors on negative overrange. There is no channel-specific scale or offset. Values around 2–4 pF are not explained by an ordinary CAPDAC range threshold.

SHLD1 follows the selected input in single-ended CAPDAC mode and SHLD2 is floating internally; the external common guard remains driven through SHLD1 for **either** CIN1 or CIN2. CIN2 is not unshielded merely because SHLD2 floats in this mode. Differential operation must not be introduced casually on this board with its externally joined shield outputs. Register and conversion review follows [TI's FDC1004 datasheet, sections 6.3–6.6](https://www.ti.com/lit/ds/symlink/fdc1004.pdf).

The application preserves `[0]`/`[1]` through raw status and calibration. `sensor_moisture()` computes `(raw_fF - dry_fF) * 10000 / (wet_fF - dry_fF)` in 64-bit arithmetic, clamps to 0–10000, and returns hundredths of a percent. SENSE2=2095 is 523 fF below dry; 2226 is 392 fF below dry. The clamp explains the displayed zero but not the poor physical response.

The encoder emits UUID FCD2, unencrypted v2 info 0x40, then two little-endian uint16 0x14 moisture objects, in SENSE1/SENSE2 order. This matches [BTHome's format and repeated-object rules](https://bthome.io/format/). No raw-capacitance-to-moisture reinterpretation occurs at the receiver. 0.2.28 removes 0x3d diagnostic count objects only. The archived 0.2.27 `carrier.c` is byte-for-byte identical to the current file; ELF disassembly for both releases is retained in the evidence folder.

Existing C driver/calibration/encoding tests, browser protocol tests, version checks, partition checks and the saved 0.2.28 DFU package validation passed. These establish software consistency, not analog behavior on either device.

## Remaining hypotheses and discriminating tests

1. **High resistance/open connection or shunt fault on the SENSE2 path**, including assembly at R31/U3 or D9 leakage. A ~2 pF reading and handling spikes do not eliminate this. With battery removed, compare electrode/TP2 → R31.1 continuity, resistance through R31, R31.2 → U3.3 continuity, and resistance to ground/shield against the SENSE1 path. Do not inject external voltage into the powered board. A shared assembly issue could affect two units even when the netlist is correct.
2. **Actual coupling differs despite full coverage**: local soil contact, coating thickness/air gap, shield coupling, return path and upper/lower geometry. Obtain hands-away settled traces under matched conditions; full burial alone does not guarantee equal electrical coupling. A controlled equal target over each electrode or equivalent soil packing can distinguish response amplitude from calibration offset. An electrode-to-shield capacitance is largely rejected, so low reported capacitance does not bound total input loading.
3. **Analog loading/settling or acquisition-order effect**. Both channels use the same resistor and code, but CIN1 is always acquired first. No live register access is exposed by the present GATT service, and there is no attached debug probe to test a different sequence. A bench-only diagnostic experiment should compare CIN1→CIN2, CIN2→CIN1, repeated same-channel conversions and independent measurement slots, with configuration/readback and completion timing logged. A fault that follows the second conversion rather than the physical electrode would justify a firmware change. None has yet been demonstrated.

TI advises input RC much less than 1 µs and places series resistance between the electrode and protection clamp ([TI ESD guidance](https://e2e.ti.com/support/sensors-group/sensors/f/sensors-forum/527553/fdc1004-esd-protection)). Both channels follow that topology. Equal resistors alone cannot explain a SENSE2-only loss; actual loading or assembly would need to differ. Do not replace this investigation with lower calibration endpoints: a 19 fF span is not established as a usable moisture response.

No firmware fix or OTA is justified by the current evidence. If a diagnostic experiment identifies an order/settling error, reproduce it, implement the smallest correction, then verify raw response on hardware in both air and soil before OTA deployment.

## Live BLE investigation

Continuous scanning caught both devices while the user confirmed both electrodes were covered:

- Soil 1: FCD2 `4001400215080366180c980a141e121400003d00003d0000`, moisture **46.38% / 0%**, battery 2712 mV, RSSI −80 dBm.
- Soil-531E: FCD2 `40015c02e407035f160c790b14050e140000`, moisture **35.89% / 0%**, battery 2937 mV, RSSI −77 dBm. No count objects, consistent with 0.2.28.

These are live advertisement observations, not new raw-capacitance measurements or fresh active-image confirmations. Initial GATT attempts timed out. The scanner's only intended write is one-byte command 0x04 (Measure-now); it does not begin or commit a settings transaction. On connection it saves configuration bytes, collects status including raw fF/CAPDAC/errors/version, and checks configuration bytes afterward. The user offered to move the boards closer, which requires taking them out of soil; samples after that move must not be mislabeled as buried.


### Nearby raw acquisition completed

After the user brought Soil #2 onto a tissue box and power-cycled it, BLE RSSI improved to about −52 dBm and GATT connected successfully. Fresh status reports 0.2.28, 2925–2950 mV, zero sample/storage errors and CAPDAC `[0,0]`. Stored settings were read before and after: the full 64-byte configuration was **identical**, including all four calibration endpoints, 900/3600 s cadence, 5000 ms window, 500 ms advertising spacing and 300 s session limit. Save count stayed zero.

100 Measure-now conversions over 129.9 seconds returned:

| Channel | Minimum | Maximum | Mean | Standard deviation |
|---|---:|---:|---:|---:|
| SENSE1 | 1904 fF | 1908 fF | 1905.44 fF | 0.64 fF |
| SENSE2 | 1981 fF | 1984 fF | 1982.65 fF | 0.61 fF |

All samples were valid, all reported errors zero and all CAPDAC values zero. This rules out a CAPDAC stepping or reported conversion-error explanation for the nearby baseline. It does not prove physical electrode continuity. A tissue box is part of the dielectric environment, so this is not a standardized free-air calibration.

A palm-near-each-pad test was requested during capture, but its execution/timing was not confirmed before the 100-sample acquisition ended; do not call the flat trace a failed palm test. A labeled, matched response test remains necessary. Comparing the previously supplied buried 3701/2226 fF with the nearby means suggests a much larger change in SENSE1, but the changed fixture, handling and timing make this less controlled than the user's Soil 1 paired observation.

Raw logs, CSV and summary are `nearby.jsonl`, `nearby-samples.csv` and `nearby-summary.json` in the evidence folder. Original in-soil advertising captures are `live.jsonl`. No firmware source, PCB, calibration, advertising interval or device name was edited; no OTA was performed.


## Follow-up: confirmed hand grip and release

The user explicitly held Soil #2 tightly, power-cycled it for connection, then confirmed setting it back on the tissue box after a release request. Fresh GATT measurements on 0.2.28 show a sustained response on both channels, followed by a return to the earlier nearby baseline.

| State | SENSE1 mean (range), fF | SENSE2 mean (range), fF |
|---|---:|---:|
| First 31 fresh samples while held (~39.5 seconds) | 3668.84 (3658–3685) | 3662.84 (3648–3686) |
| Last 20 samples after release | 1913.05 (1912–1914) | 1984.35 (1984–1985) |

Across 112 fresh samples, all measurements were valid, both CAPDACs remained zero, all sample/storage errors were zero and the save count stayed zero. The configuration read at connection matched the prior verified settings. The collector was stopped intentionally with SIGINT once the returned baseline was stable; its final full configuration read was not reached. No configuration transaction or OTA was sent.

This substantially weakens the idea of a stuck/unresponsive CIN2 conversion and excludes a software clamp that always forces SENSE2 to zero: its initial held advertisement itself encoded nonzero second moisture. It does **not** prove full electrode continuity or rule out shared coupling, because both pads and the board were gripped together. It does not by itself distinguish local soil contact/coating, shield/return geometry, leakage or order-dependent analog behavior under soil loading. The next discriminating physical experiment should expose each pad separately to the same controlled target, or repeat matched soil packing with reliable nearby BLE. Do not infer a new soil calibration from hand capacitance.

Evidence: `held.jsonl`, `held-markers.jsonl`, `held-samples.csv`, `held-summary.json`, and `held-response.png` in `output/sense2-investigation-2026-09-25/`.
