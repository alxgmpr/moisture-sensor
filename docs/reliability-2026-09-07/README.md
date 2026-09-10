# Reliability changes — 7 September 2026

The maintained PCB, schematic, BOM, assembly package and a new real-hardware qualification application have been updated. This closes concrete layout, component-selection, firmware and export issues from the [audit](../audit-2026-09-06/README.md). It does **not** establish first-pass hardware qualification: there is no assembled board available for measurement, and the actual coating, soil conductivity and final enclosure are not specified.

## Implemented

| Finding | Change | Verification / remaining limit |
|---|---|---|
| D8/D9 ESD ground paths ran through the sensing region | Each clamp now has a 0.5 mm top connection to a nearby ground via and a dedicated 0.9 mm wide In1 ground finger connected to the electronics plane. Conflicting shield stitching was removed locally. | Filled-plane regression, native DRC and visual copper inspection. The return still has finite inductance; this is not an ESD survival guarantee. |
| Marginal or unqualified reservoir selection | C21 **and** C23 now use Murata **GRM158R60J226ME01D**, 22 µF, 6.3 V, X5R, 0402, LCSC **C3894351**, the exact part listed in Nordic nwp_058 tables 6/8. | PCB/schematic/BOM agree. Nordic-reference selection is stronger evidence than nominal µF; a guaranteed bias/temperature/aging minimum is still not established. No automatic substitutions. |
| PMIC/sensor behavior existed only as requirements | Added [carrier bring-up firmware](../../firmware/carrier-bringup/README.md): real FDC1004/SHT45 reads, correct load-switch configuration, 3.3 V selection, force-HP through sensing/radio with actual-state confirmation, voltage checks, 40 mA sensor-output OCP, no heater, bounded I²C/conversion waits, automatic CAPDAC selection in single-ended mode, MCU and PMIC watchdogs, verified shutdown before System OFF. | Host conversion/fault-injection tests and complete nRF Connect SDK 3.2.2 build pass. Hardware timing, noise, power and wake behavior remain to be measured. |
| Carrier could be mistaken for the simulated DK application | New carrier-specific devicetree removes DVK peripheral conflicts, sets actual I²C pins and provisional crystal loading; raw readings go to RTT and `ProbeQA` advertises after successful measurements. | Generated devicetree/config retained. No invented soil percentage or battery SOC; calibrated BTHome integration remains future work. |
| Fiducials included in component placement export | FID1–FID4 now excluded from position files while retained as copper/mask fiducials. | Placement regression and exact BOM/CPL reference match. |
| Stale Gerbers could enter a new archive | Exporter now selects exactly the 13 required current-board files rather than every matching extension in a reused directory. | Regression includes a complete stale board set and a missing required file. |
| Documentation described backing shield absent from actual copper | Corrected LAYOUT.md, capacitor BOM and hardware status. | Current layers have no shield directly below either electrode on any lower layer. |

The two ground fingers add **8.721 mm²** of F.Cu shield / In1 GND projected overlap and **8.902 mm²** of In2 shield / In1 GND overlap. Using εr=4.2 and the 0.0994/1.265 mm dielectric gaps gives approximately **3.5 pF combined**, before fringing. Do not double-count bottom shield behind In2 as another independent parallel plate.

[Four copper layers](layers.png) · [ESD return detail](layers/nrf-moisture-sensor-GND-detail.png) · [schematic](schematic.png) · [assembly rendering](assembled.png). The battery-holder model remains a substitute, so rendering cannot certify the actual holder/enclosure fit.

## What simulation established—and did not

[Simulation inputs and reproduction instructions](../../simulation/README.md) · [plots](simulation.png) · [probe sweep CSV](probe-sweep.csv).

**openEMS:** Both source-return fixture runs reached −40 dB energy decay. At 200/300/500 MHz the baseline apparent inductance is 8.19/8.46/8.30 nH and the revised fixture is 6.29/6.24/6.10 nH. These are fixture values, including the artificial reference conductor. There is no mesh-convergence proof, and the baseline port extraction becomes non-passive near the high-frequency limit. The numerical result supports investigation of the shorter path; it does not quantify immunity improvement. Do not infer IC pin voltage or IEC pass levels from it.

**Probe electrostatics:** A separate 2-D finite-volume solver, checked against an analytical parallel-plate problem, gives approximately 0.45–14.6 pF across the lossless cases with a 30 mm outer ground boundary. A finer mesh changes estimates by up to 9.5%; moving that boundary changes them by up to 24.6%. End effects and soil conductivity are absent. The range is not evidence that a wet/saline probe will remain within the FDC range.

**Conductive-soil case:** Current exposed front/back SHLD zone area is approximately 546 + 595 = **1,141 mm²**. If both faces see grounded conducting material through a uniform coating, `C ≈ ε₀ εr A / t`. This deliberately strong coupling case gives:

| Minimum coating thickness | Shield coupling at εr=3 | Shield coupling at εr=4 |
|---|---:|---:|
| 0.05 mm | 606 pF | 808 pF |
| 0.10 mm | 303 pF | 404 pF |
| 0.25 mm | 121 pF | 162 pF |
| 0.50 mm | 61 pF | 81 pF |

These estimates omit edge fringing and other loads. At εr=4, a single 480 mm² sense face through 0.10 mm coating is about **170 pF**, beyond the nominal CAPDAC plus measurement range. At 0.25 mm it is about **68 pF**, before other coupling. This is why coating is part of the electrical design.

A useful **provisional process target is ≥0.25 mm actual cured thickness**, with a known low-water-absorption material whose wet permittivity remains ≤4, covering faces, edges and probe test points. It is not a guaranteed specification: verify thickness after cure, adhesion, abrasion, voids, water uptake and the assembled electrical load. Do not coat the SHT45 membrane. If the material/process cannot sustain these assumptions, change electrode/guard area or coating thickness before treating the design as qualified.

The integrated BL54L15 antenna lacks an available conductive geometry/feed/material model here. A STEP visualization is not an antenna model. openEMS cannot honestly supply its enclosed S11/efficiency from the supplied files.

## Still open before calling this a reliable field design

1. **Exposed SHLD protection:** D10's TVS clamp voltage is above FDC1004 pin limits, with no shield series limiter. Existing CIN resistors also need transfer-function and ESD testing. Adding an arbitrary diode/resistor can load or destabilize the driven shield; no unverified replacement was fitted. Test both polarities and powered-on/off conditions with the actual coating.
2. **FDC powered-off I²C leakage:** SDA/SCL remain pulled to the always-on rail. Absolute maximum pin tolerance does not prove low leakage with VDD=0. Measure the off rail/current; add a qualified isolation arrangement if it back-powers. Firmware shutdown alone cannot establish this.
3. **Radio supply:** HP scheduling is implemented, but measure at U1 during TX and sensor switching against Ezurio's 10 mV supply-noise requirement. C3/C25/C27 plus the module must remain within the PMIC's output capacitance window. Reservoir DC-bias verification and output-load stability are not replaced by the PMIC ADC.
4. **Battery fault protection:** Q1 handles reverse insertion; there is still no battery fuse, rechargeable-cell OVP or whole-board cutoff. The new LDOSW current limit covers only FDC power. A fuse that cannot trip from a CR2032 is not useful protection. Use the specified primary cell and validate short/fault behavior with the chosen cell. J4 is voltage reference, not an authorized supply input with a coin cell fitted.
5. **Mechanics/RF:** Check the actual battery holder, lid, screws and wet probe against antenna clearances; use strain relief at the probe shoulder and verify seals. Measure OTA performance on low/mid/high channels with the closed enclosure. Retain solid electronics ground planes; no ground bead or common-mode choke was added because the present design has no external differential cable requiring one.
6. **Calibration and aging:** Characterize raw C and CAPDAC transitions, dry/wet/saline media, coating absorption and temperature. The current qualification image does not implement calibrated BTHome moisture reporting.

## Verification and deliverables

- Native KiCad **10.99.0-3619-g0ef48b972f**: zero DRC errors, zero unconnected items, zero schematic-parity issues; zero ERC errors. Ten library-geometry DRC warnings and ten library-symbol ERC warnings remain. Existing ignored rule categories are recorded in the JSON; a clean check is not product certification.
- Repository tests, host firmware tests (including undefined-behavior sanitizer) and the electrostatic analytical check pass. Firmware builds to **84,608 bytes flash / 21,624 bytes RAM**.
- [Flashable qualification image](firmware/carrier-bringup.hex), generated [devicetree](firmware/zephyr.dts), configuration and build log retained. No board was flashed or physically tested.
- Refreshed [JLC quote package](../../production/jlc-economic-quote/QUOTE.md): 36 fitted components, 20 BOM groups, matching CPL, 13-file Gerber ZIP, schematic and source hashes. U1 remains separately sourced/hand fitted and absent from JLC BOM/CPL/paste. No order has been placed.

For the first assembly, record battery-equivalent current-limited startup, U1 supply ripple, FDC off-state leakage, watchdog recovery from a stuck bus, repeated independent one-minute wakes, and raw capacitance/shield behavior across the intended environments. Perform ESD and RF checks with the final mechanics. These measurements are the remaining evidence needed to turn a plausible first revision into a dependable sensor.

## Primary references

- [Nordic nPM2100 datasheet and design resources](https://www.nordicsemi.com/Products/nPM2100/Documentation); local nwp_058 hardware design guidelines tables 6/8 for the reservoir selection.
- [Murata exact capacitor reference specification](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM158R60J226ME01-01A.pdf).
- [TI FDC1004 datasheet](https://www.ti.com/lit/ds/symlink/fdc1004.pdf), single-ended/CAPDAC configuration, pin limits and 400 pF shield limit.
- [Sensirion SHT4x datasheet](https://sensirion.com/resource/datasheet/sht4x), conversion/CRC and heater commands.
- [Ezurio BL54L10/BL54L15 datasheet](https://www.ezurio.com/documentation/datasheet-bl54l10-and-bl54l15-series), supply and antenna integration.
- [Nordic nPM2100 timer](https://docs.nordicsemi.com/r/bundle/ps_npm2100/page/chapters/core_components/timer/doc/frontpage.html), watchdog versus sleep-mode behavior.
