# Board protection, derating and EMC audit — 2026-09-06

The current board passes connectivity checks, but I would not release it as a qualified field product yet. The most actionable additions to the previous reviews are the probe ESD return routing, exposed shield protection, firmware restrictions imposed by the tied shield outputs, and the mismatch between the actual probe copper and the documented sensing geometry.

This is a read-only design audit: no maintained schematic, PCB, BOM, or firmware was changed. KiCad application replacement was coordinated with the updating task. Fresh checks used KiCad 10.99.0-3619-g0ef48b972f. No hardware measurement or full electromagnetic simulation is claimed.

## Findings, in priority order

### 1. Probe ESD returns take a long route through the sensing area — P1, confirmed geometry

D8/D9 at y112.2 sit below the solid electronics ground boundary at y106.9. Their ground vias do **not** drop directly into a ground plane there: both inner layers are SHLD in this region. D8 ground runs 1.96 mm on F.Cu, through a via, 3.82 mm on B.Cu, through another via, then onward to ground. D9 returns through about 5.43 mm of F.Cu before joining that path. This contradicts the older protection report's description of local vias returning directly to In1 ground.

Those conductors can be perfectly connected at DC while allowing substantial ESD ground bounce. ESD current also crosses the analog input region. Relocate the clamp/resistor boundary toward the electronics ground, or deliberately provide a short, broad ground return corridor and recalculate the sensing parasitics. Do not simply convert probe shield vias to ground. Validate both polarities with the finished coating and the FDC powered on and off.

Evidence: [fresh copper layers](layers.png), [geometry extraction](geometry.txt), current D8/D9 ground traces and vias at (68.8,110.238616) and (71.5,107.538616) mm.

### 2. D10 does not establish safe shield-pin voltage — P1, unresolved protection coordination

The netlist connects D10, TP3, U3.1 and U3.6 directly. Unlike the CIN paths, it has no series current limiter. The fitted TPD1E01B04DPY is a bidirectional transient suppressor, not a 3.3 V precision clamp: typical breakdown is 6.4 V, with typical TLP clamp levels of 7 V at 1 A and 15 V at 16 A. Its IEC component rating does not certify this circuit. The exact DPY capacitance is 0.20 pF typical / 0.23 pF maximum at the stated test point; the older 0.18 pF description belongs to DPL. [TI suppressor datasheet](https://www.ti.com/lit/ds/symlink/tpd1e01b04.pdf).

FDC analog pins are limited to −0.3…VDD+0.3 V and 3 mA input current. Review secondary protection and the residual waveform at the IC, especially with VDD discharged. R30/R31 help CIN protection, but 5.1 kΩ is not proof of compliance: for illustration, (15−0.3)/5100 ≈ 2.88 mA when unpowered, before overshoot and tolerance. A resistor also does not establish pin voltage unless a clamp conducts. [TI FDC1004 datasheet](https://www.ti.com/lit/ds/symlink/fdc1004.pdf).

Do not add a large shield resistor blindly: it can spoil shield tracking. Compare revised protection on prototypes against sensing noise, drift and ESD recovery. Ordinary resistor wattage does not establish nanosecond pulse survival.

### 3. C21 is still marginal; C23 and total VOUT remain unqualified — P1

The current source still selects these exact capacitors:

| Node | Parts | Check / action |
|---|---|---|
| VBAT | C21 10 µF 6.3 V X5R, CL05A106MQ5NUNC; C22 1 nF | Require ≥3.5 µF effective. Exact-part typical DC-bias graph gives roughly 40% retention at fresh-cell voltage: 10×0.40×0.8≈3.2 µF, before further allowances. Qualify or revise C21. |
| VINT | C23 22 µF 6.3 V X5R, GRM155R60J226ME11D; C24 1 nF | Require ≥3.5 µF effective. At −20% tolerance it needs ≥19.9% retention before temperature/aging allowance. Exact guaranteed minimum is not established by the retrieved information. |
| VOUT | C3 10 µF + C25 2.2 µF + C27 0.1 µF, plus module | 12.3 µF nominal external; 14.75 µF at positive listed tolerances before bias/temperature/module. Check the complete 0.7–15 µF effective range. This upper screening bound is not proof of failure. |
| FDC switched rail | C26 1 µF X7R + C28 0.1 µF X7R | Values appropriate; C28 is nearer U3.8. This branch comes from VINT through LDOSW and is not directly included in the VOUT sum. Test turn-on load independently. |

Re-inspected the [exact C21 characteristic plot](../component-review-2026-09-05/c21-characteristics.png). Its separate biased-temperature graph is less pessimistic than multiplying separate typical curves, so the calculation above is a screening concern, not a guaranteed failing lot. Obtain combined bias/temperature behavior and aging allowance. Samsung confirms the selected part is 0402, ±20%, X5R to +85°C; do not infer a +125°C product rating from the sensor ICs. [Samsung part page](https://product.samsungsem.com/mlcc/CL05A106MQ5NUN.do).

The 6.3 V capacitors have useful voltage-rating margin on 3.3 V rails, but voltage rating and effective capacitance are separate checks. Sources: local [Nordic hardware guidelines](../../doc/datasheets/nPM2100_HW_Design_Guidelines_nwp_058.pdf), §3.2–3.4, and [nPM2100 datasheet](../../doc/datasheets/nPM2100_Datasheet_v1.0.pdf), Table 10. Component lookup confirmed C23 identity, not its bias curve. Larger capacitance belongs on VBAT/VINT when justified; arbitrary extra VOUT bulk is inappropriate.

### 4. Firmware-dependent safeguards are not implemented in the checked application — P1

[main.c](../../firmware/bthome-sensor/src/main.c) calls `sim_values()` and advertises the result. It has a SoC watchdog, but no actual PMIC/sensor sequence in this path. The [port requirements](../../firmware/BL54L15-port.md) are requirements, not implementation evidence.

The carrier implementation needs to establish 3.3 V before enabling FDC; configure LDOSW as a load switch; force and settle HP for measurement/radio; enforce heater/radio load policy; handle a stuck I²C bus with bounded timeouts; and implement low-cell lockout/retry behavior. Configure the PMIC watchdog/recovery deliberately and reapply configuration after PMIC power-cycle resets. SYSGDEN is grounded, disabling the startup boot monitor. A host watchdog reset alone does not necessarily clear a wedged always-powered peripheral. Test reset causes and recovery, including SHT bus lock and interrupted PMIC writes.

U3.1 and U3.6 are tied together: permit single-ended measurements only; do software subtraction if needed. Differential mode drives the shield outputs for different channels. Also, the FDC's independent 6 V SDA/SCL absolute maximum does **not** specify unpowered leakage. Measure the off-rail voltage/current and obtain manufacturer confirmation before claiming zero back-powering. [TI FDC1004 datasheet](https://www.ti.com/lit/ds/symlink/fdc1004.pdf), §§5.1, 5.6 and 6.3.1.

### 5. Battery capability, fault containment and heater policy need a defined cell — P1 for field release

No fuse, PTC, battery-side current cutoff or sustained overvoltage cutoff is fitted. Q1 blocks reverse insertion; it is not a fuse or complete reverse-current barrier. D1 is directly across the raw cell, and C21/D2 are upstream of the PMIC. A short there bypasses downstream load-switch protection. Do not interpret the PMIC's valley-current limiter as a guaranteed battery safety current cutoff. Review the exact cell's short-circuit behavior and the entire fault path.

A fuse/PTC is a **conditional design decision**, not automatically mandatory or automatically useful. Its guaranteed clearing/trip curve must operate at available cold/depleted-cell fault current while tolerating normal converter pulses and acceptable series drop. A PTC that never trips provides little protection. If fitted, place protection sufficiently close to the positive contact to cover downstream shunts; an upstream D1 short would otherwise remain unprotected. Consider an independently acting low-leakage disconnect if fault tests require it. Do not use a narrow PCB trace as an improvised fuse.

J4.1 connects directly to +3V3: treat it as VTref only. External powering/backfeed with a cell installed requires a separately validated power path; Q1 alone does not guarantee no charging of the primary cell. Specify CR2032 chemistry and exclude rechargeable lookalikes with higher voltage.

The heater can dominate the cell load: 100 mA at 3.3 V is 330 mW, requiring about 194 mA at 2.0 V with an illustrative 85% efficiency, before other loads. A CR2032 label or holder rating does not establish this capability. Keep the heater disabled until qualified; use the lowest effective setting and allowed duty cycle. See [prior load analysis](../power-review-2026-09-05/README.md) and [SHT4x v7.3 Table 4](../../doc/datasheets/sensirion-sht45/HT_DS_Datasheet_SHT4x_V7.3.pdf).

### 6. Probe field geometry and shield load are not qualified — P2

The current filled copper has **zero projected shield overlap beneath either 16×30 mm electrode on all three lower layers**. Shield surrounds the electrodes; it does not cover their backs. Both inner layers carry SHLD around the probe openings. This differs from LAYOUT.md's continuous backing-shield description and its old 6 pF ground-overlap estimate. It is not automatically wrong for soil sensing, but calibration and backside-object sensitivity must match this actual construction.

Projected shield-fill/ground-fill overlap is also zero in this snapshot; that does not imply zero shield load. Fringing, tracks, exposed outer shield, coating and conductive wet soil remain. For scale only, a hypothetical 600 mm² surface facing a conductor through 0.05 mm of εr=3 coating gives C≈319 pF. That is already comparable to the 400 pF shield capability before other contributions. This is a sensitivity example, not an extracted assembled capacitance. Measure shield amplitude/phase and sensing range in dry/wet/saline media with the final coating and mechanical placement.

R30/R31 also alter the measurement transfer function. At 100 pF their RC is 0.51 µs; validate calibration and settling across actual input range instead of assuming a simple DC RC model proves switched-capacitor accuracy. Inspect coating coverage over edges, vias and TP1–TP3; bare test contacts and moisture tracks can defeat otherwise insulated electrodes. Keep sensor airflow and its membrane free of coating/flux contamination.

### 7. Antenna mechanics and supply noise remain release risks — P1 qualification

The module is at the board edge with all-layer copper exclusion. DRC finds no keepout violation. This does not establish enclosure RF performance: cell/holder metal, screw material, lid, coatings and wet soil are outside those copper rules. The holder model is a visualization substitute, so rendered fit is not physical clearance evidence. The prior mechanical review already identified preferred metal-spacing compromises.

Ezurio requires antenna keepout free of copper and metal hardware and specifies a tight supply-noise condition. Compare the actual assembled module supply against 10 mV during TX/RX; nPM2100 LP/ULP's typical 70 mVpp makes HP scheduling necessary to investigate, not sufficient proof. [Ezurio integration datasheet](https://www.ezurio.com/documentation/datasheet-bl54l10-and-bl54l15-series).

Test closed assemblies with the cell, intended screws and representative soil on low/mid/high radio channels and multiple orientations. Do not add a host antenna choke or matching network: this module has an integrated antenna and no host RF feed. Keep mechanical loads off the module and support the probe shoulder so insertion force does not flex the MLCC/IC region. Enclosure seam capture and weather sealing are still unresolved in the [mechanical review](../../output/product-video/enclosure-review.md).

## Ground planes, beads and common-mode chokes

The electronics have continuous GND on both inner layers, no inner signal/power tracks, and extensive stitching. Preserve that. Multiple connections in a ground plane are useful high-frequency returns, not a reason to cut the plane into stars. In normal battery operation there is no wired earth loop; a debugger, oscilloscope and wet environment can introduce new paths during testing.

Signal transition vias are roughly 1.5–2.8 mm from the nearest ground via in this extraction. Add closer return vias where practical at SWD/clock transitions, prioritizing fast edges, without violating the antenna exclusion. Those distances are a review heuristic, not a compliance threshold. The nPM switch route is short and local; wide power traces are not the main remaining limitation.

| Candidate | Recommendation |
|---|---|
| Ground bead / split analog ground | Do not add. It impedes return current and can worsen coupling. |
| Module-supply bead | Optional tuning provision after measuring spectrum. Check impedance at the actual noise frequencies, DC current/bias, DCR, resonance/damping and load transients. Preserve PMIC local output capacitance and qualify the whole network. |
| Bead in VBAT | Avoid an unmodeled input filter: the coin cell already has high impedance. |
| Beads on CIN/SHLD | Do not add by default; they alter a precision capacitive interface. |
| Common-mode choke | No present external differential data/power cable justifies one. SDA/SCL are not a differential pair. Reconsider at a future cable boundary if common-mode testing identifies a problem. |

Ferrite beads can resonate with ceramic capacitors and lose impedance under DC bias; a nominal “600 Ω at 100 MHz” value is not a cure for low-frequency burst ripple. [Analog Devices AN-1368](https://www.analog.com/en/resources/app-notes/an-1368.html).

## Focused prototype and EMC test plan

1. **Power/derating:** exact capacitor model/lot checks at operating voltage and temperature; cold-start and hot-plug waveforms; emulator voltage/impedance sweeps followed by specified real cells; measure rails at C21/C23/C25/U1/U3/U4. Record extrema, source current and mode transitions. Test heater separately before concurrency.
2. **Sensing:** known reference capacitors, both channels, final coating and dry/wet/saline media; inspect shield tracking, full-scale/CAPDAC headroom, hysteresis, temperature drift and radio-on/off error. Repeat with objects behind the electrodes.
3. **Fault/recovery:** staged current-limited fault characterization, reversed battery, FDC off-state leakage, stuck SDA/SCL, failed startup, brownout and watchdog recovery. Battery abuse/short testing belongs in a controlled fixture using the cell supplier's guidance, not an improvised direct short.
4. **EMI pre-scan:** near-field H/E scans at the PMIC/inductor, digital routes and probe; compare sleep, conversion, TX and heater states. Radiated emissions and receiver performance should include final assembly, operating modes and supply extremes. Watch for false measurements and permanent sleep-current increases, not just resets.
5. **Immunity:** agree product-specific ESD and radiated-RF targets with the lab; exercise accessible battery/debug/probe points and enclosure seams, powered and unpowered. Separate direct strikes from indirect coupling. Choose EFT/surge/conducted-RF tests according to actual external ports and environment; a battery-only board does not automatically need every mains-port test.
6. **Product completion:** validate sealing, insertion/drop/bending and cell retention. If sold as a US consumer product, determine applicability of coin-cell compartment and labeling rules even if shipped without a cell. [CPSC guidance](https://www.cpsc.gov/Business--Manufacturing/Business-Education/Business-Guidance/Button-Cell-and-Coin-Battery). Final RF/EMC obligations depend on intended markets and module integration conditions; module approval alone is not a host-product test report.

## Verification record

- [DRC](drc.json): zero errors, zero unconnected items, zero schematic parity issues; ten footprint-library mismatch warnings.
- [ERC](erc.json): zero errors; ten symbol-library mismatch warnings.
- [Fresh netlist](netlist.xml), [schematic render](schematic.png), [all four copper renders](layers.png), [source hashes](source-sha256.json), [geometry details](geometry.txt).
- The [assembled render](assembled.png) uses a temporary copy with U1’s DNP and position-file exclusion flags cleared for visibility. It is visual inspection only, not solid-interference certification; cell/enclosure geometry is not included.
- Existing library-copy mismatches need reconciliation before manufacturing without overwriting deliberate pad modifications. No new tests were written for this read-only audit.

Recommended next design work: resolve C21, shorten the probe clamp returns, qualify shield protection, and implement the real carrier power/sensor sequence. Then use measurements to decide whether a battery cutoff or module-supply filter is warranted.
