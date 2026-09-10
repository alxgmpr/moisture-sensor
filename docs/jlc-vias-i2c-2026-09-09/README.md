# JLC four-layer via rules and powered-off I²C — 9 September 2026

The preceding review mistook conservative project rules for JLC fabrication limits. **The reported 0.50/0.30 mm vias and 0.227–0.240 mm via-hole clearances are within JLC's published rigid multilayer capability.** No copper resizing or rerouting was necessary. D8/D9 return routing is accepted by the user and remains unchanged.

## Via capability and implemented rules

Source checked: [JLCPCB rigid PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), drilling and trace tables. This board is four-layer, 1.6 mm, 1 oz external copper; flex-board limits and plated component-lead annular rings are different specifications.

| Check | JLC published capability | Maintained project rule |
|---|---|---|
| Through-via drill | 0.15 mm minimum; 0.20 mm preferred minimum | 0.20 mm retained |
| Via pad minus hole diameter | 0.10 mm minimum; 0.15 mm preferred | 0.20 mm minimum diameter difference, i.e. **0.10 mm radial ring**; changed from 0.13 mm ring |
| Via-hole to copper | 0.20 mm, including inner layers | **0.20 mm**, changed from 0.25 mm |
| Via hole-to-hole gap | 0.20 mm | 0.20 mm retained |
| Plated component-pad annular ring, multilayer 1 oz | 0.15 mm minimum; 0.20 mm recommended | Separate 0.15 mm minimum |
| Component PTH hole to copper | 0.28 mm outer; 0.30 mm inner | Conservative separate 0.30 mm rule on all layers |
| Pad hole-to-hole gap | 0.45 mm | Separate 0.45 mm rule |

A 0.50 mm via pad and 0.30 mm hole give (0.50−0.30)/2=0.10 mm radial ring, exceeding JLC's preferred 0.075 mm radial value. Our 0.50 mm minimum via diameter also remains more conservative than the factory capability. Existing 0.50/0.20 and 0.60/0.30 routing defaults remain valid. JLC's extra-cost note covers 0.15 mm drills and 0.20/0.25 mm drills with pad diameters below 0.45 mm; those combinations are unnecessary here.

U2's nine drilled pad-17 features are **thermal vias embedded in a footprint**, not holes for component leads. They retain via-class hole clearances. Ordinary plated pads still get the stronger rules. No severities or DRC exclusions were disabled.

Changed only the relevant rule/project settings and corrected the unsupported leakage statement in HARDWARE.md. Source PCB and schematic were not edited. The [fresh DRC](drc.json) and [native injection tests](injected/checks.json) provide validation. The injection test deliberately reduces a via ring, reduces a hole clearance, and changes one thermal-via pad into a non-exempt drilled pad: all three are correctly rejected. Reproduce with `python3 docs/jlc-vias-i2c-2026-09-09/check_rules.py`.

## What is actually known about FDC1004 leakage

The [FDC1004 datasheet](https://www.ti.com/lit/ds/symlink/fdc1004.pdf) permits SDA/SCL voltages independent of VDD in its absolute-maximum table, but does not specify an Ioff guarantee at VDD=0. Its interface electrical characteristics assume VDD=3.3 V. No explicit unpowered SDA/SCL leakage guarantee was found in the TI support searches either. Thus there is no justified numeric leakage prediction for the present board, and no evidence here that it necessarily back-powers.

The main rail feeds R22/R23 and the shared MCU/PMIC/SHT/FDC bus. The FDC supply alone is switched. A leakage path from its bus pins could therefore draw current throughout sleep. The PMIC's roughly 2 kΩ output-discharge path can hold the FDC rail near zero while sinking that leakage: rail voltage alone is insufficient evidence.

For scale, 1 µA continuously is 8.76 mAh/year at that rail. At a 3.3 V rail, illustrative 3.0 V cell and 90% conversion efficiency, that is about 10.7 mAh/year from the cell. These numbers describe the cost of an assumed leakage, not a measurement. Leaving the FDC powered is unattractive: 29 µA typical standby alone is approximately 254 mAh/year at its supply, before conversion losses and other loads.

## Ways to guard against it

### A. Separate FDC bus — preferred if two MCU pins can be routed conveniently

Keep the existing main bus and pull-ups for PMIC and SHT. Move only FDC SDA/SCL onto two spare compatible MCU pins with two pull-ups to +3V3_FDC_SW. Disable internal pull-ups and keep the new pins disconnected/high impedance whenever FDC power is off; never drive them high from the main rail. Configure a valid same-port TWIM instance/pin combination during implementation, or use open-drain software I²C at 100 kHz.

This removes the always-on pull-up feed to FDC without another always-powered IC. The PMIC stays reachable and an FDC bus fault does not block PMIC power-cycle commands. Costs: two GPIOs, two pull-ups, routing and firmware changes. Boot/reset/System OFF pin states must be verified. It is a proposal, not an implemented pin assignment.

### B. Two discrete MOSFETs — small change while keeping the shared bus

Split only the FDC branch. On each line place an N-channel MOSFET with **drain on the always-on bus, source on the FDC bus, gate on +3V3_FDC_SW**, and add an FDC-side pull-up to that switched rail. R22/R23 remain on +3V3. With FDC power off, the gate/source fall and the body diode blocks conduction from the upstream bus into the FDC side. Reverse orientation would defeat that isolation.

This is the powered-down-section isolation circuit in [Nexperia AN10441](https://assets.nexperia.com/documents/application-note/AN10441.pdf). It works with equal nominal bus voltages too. Verify the actual VINT-fed FDC rail versus VOUT, transition behavior, MOSFET off leakage over the intended temperature range, gate threshold/on-resistance, bus capacitance and low-level margins. The source-side supply must not materially exceed the drain-side supply in normal operation. A generic MOSFET name alone is not a guaranteed leakage budget.

With an added 4.7 kΩ pull-up on the branch, a low level sinks approximately 1.4 mA total at 3.3 V through the two pull-ups. At 100 kHz, each segment's 30–70% RC rise time is approximately 0.8473·4.7k·C: 100 pF gives 0.398 µs. Check the actual bus waveforms; this is not a full switching simulation. The extra pull-ups cost current only during low states and the powered-off branch remains separate. While FDC is powered and stuck low it can still hold the shared bus low, so retain PMIC watchdog recovery.

### C. Bidirectional bus switch — useful, but inspect the right leakage rating

Use a switch with explicit powered-off isolation and specified leakage at VDD=0 if powering it from the switched rail. Control sequencing must keep the FDC disconnected until its supply is valid and disconnect it before shutting down. Keep upstream pull-ups powered and add downstream pull-ups as required.

I checked [TI TMUX1511](https://www.ti.com/lit/ds/symlink/tmux1511.pdf) as a concrete example. It supports bidirectional I²C switching and powered-off isolation, but its attractive ±10 nA specification is only at 25°C and signals up to 3.0 V. The applicable up-to-3.6 V/full-temperature limit is **±2 µA per I/O**. Its 37 µA typical powered supply current also argues for switched, not always-on, power here. It is a functional isolation candidate, not a recommendation for a guaranteed sub-microamp sleep budget.

An always-on ultralow-Iq analog switch is another topology, but then check switch-off channel leakage, supply current and control-input current together. “Fail-safe logic” on a control input is not equivalent to powered-off protection on the bus terminals.

### What does not solve this cleanly

- Moving the existing shared pull-ups to FDC power creates a PMIC boot deadlock.
- Holding SDA/SCL low through sleep burns approximately 3.3/4.7k=0.70 mA per line in the existing pull-ups.
- Larger pull-up/series resistors trade leakage current against rise time and logic levels; they do not establish isolation.
- A bleeder on the FDC rail hides phantom voltage but still consumes the injected current; the PMIC already provides discharge.

## Measurement that decides whether isolation is needed

On an isolated FDC breakout or reworkable prototype, hold FDC VDD at 0 V with a sinking instrument or ground connection, then apply 3.0/3.3 V independently to SDA and SCL through known resistors. Record both line currents and current entering the VDD clamp. Test both-high and each high/low combination, powered-to-off transitions and the intended hot temperature. Wait for decoupling transients to settle. Then repeat with the actual PMIC discharge state and verify whole-board battery current.

For a 4.7 kΩ pull-up, 100 nA gives 0.47 mV drop and 1 µA gives 4.7 mV. Measuring across the shared pull-ups alone includes the PMIC, SHT and MCU input currents: isolate the FDC contribution before blaming that IC. A provisional target of ≤0.1 µA combined FDC-off bus leakage would keep this path small relative to the board's sleep budget; the final target should follow the required service life.

**Recommendation:** retain power gating. If changing the layout now, prefer a separate FDC bus when pin routing is practical, or the two-FET branch when minimal routing/firmware change matters more. Otherwise measure the present device before adding parts. No I²C circuit modification or part substitution was made in this follow-up.
