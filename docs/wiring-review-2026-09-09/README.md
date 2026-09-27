# Wiring and pre-fabrication review — 9 September 2026

**Follow-up supersedes the fabrication-blocker conclusion below:** [JLC via capability and I²C leakage review](../jlc-vias-i2c-2026-09-09/README.md). JLC's rigid four-layer via limits permit the reported geometry. Correcting the overly conservative rules removes those errors without changing copper. The user also accepted the D8/D9 return layout. The original measurements below remain a historical record, not the current release decision.

**Do not release the current files to fabrication unchanged.** No unintended net short, missing routed connection, or schematic/PCB connectivity mismatch was found. There are concrete fabrication-rule failures and a probe-protection layout regression, plus electrical behaviors that need prototype qualification.

This review does not modify the maintained design or firmware. It checks the current files rather than relying on older audit conclusions. Source identifiers are in [source-sha256.json](source-sha256.json). Evidence: [DRC](drc.json), [ERC](erc.json), [netlist](netlist.xml), [schematic](schematic.png), [copper](copper.png), [assembly view](assembly.png), [hardware tests](tests.txt), [firmware host tests](firmware-tests.txt).

## Fix or resolve before sending fabrication files

### 1. P1 — Via geometry fails the board's fabrication rules

Fresh native KiCad DRC with zone refill, schematic parity and all severities reports **205 errors**:

- **199 annular-width errors:** 0.100 mm measured against the project's 0.130 mm minimum. Examples include PMIC_INT vias at (67.52,102.69) and (76.19,58.54) mm and numerous ground stitching vias. A 0.50 mm pad around a 0.30 mm drill has a nominal 0.10 mm ring. For that drill, a 0.56 mm diameter is the arithmetic minimum for the present rule; 0.60 mm provides additional nominal margin. Any resizing needs a fresh clearance check.
- **Six hole-to-copper clearance errors:** 0.227–0.240 mm against 0.250 mm. These occur around the SCL via at (68.825,101.800), reset via at (71.410,99.325), and SDA via at (68.175,102.200) mm, involving SDA, PMIC_INT and the switched FDC supply traces.

Resolve the geometry or obtain explicit fabrication capability for the intended stackup and make the rules accurately reflect it. A netlist match does not establish adequate drill registration margin. Do not simply suppress these failures.

### 2. P1 — D8/D9 local ESD ground returns have regressed

The clamps remain correctly connected to ground electrically, but the nearby ground-plane vias/fingers from the 7 September implementation are absent. Their present 0.4 mm front-layer traces are:

- D8 ground: (69.080,111.290) → (68.842,111.290) → (66.400,108.848) → (66.400,106.370), about **6.17 mm** of drawn trace.
- D9 ground: (72.480,111.290) → (72.730,111.290) → (75.070,108.950) → (75.070,106.410), about **6.10 mm**.

The traces meet the electronics ground before their final endpoints, so those lengths are not an extracted high-frequency return impedance. Nevertheless, they clearly replace the former local plane connections with a long return through the analog region. The existing `test_esd_return_planes` test fails at D8; direct inspection confirms the missing local return for D9 too. See [four-layer detail](esd-returns.png).

Restore a short, broad return to electronics ground or move the protection boundary toward that ground. Recheck added sensor/shield capacitance. The signal topology itself is now electrode → R30/R31 → CIN with D8/D9 on the CIN side, consistent with [TI's placement guidance](https://e2e.ti.com/support/sensors-group/sensors/f/sensors-forum/527553/fdc1004-esd-protection).

### 3. P1 — Saved manufacturing package is from a different design

Every hash in `production/jlc-economic-quote/source-sha256.json` differs from the corresponding current PCB, schematic, project and rule file. Its 7 September clean-DRC statement cannot release this revision. Regenerate Gerbers/drills/BOM/CPL and assembly instructions together after the fixes, then inspect those actual outputs. U1 is deliberately DNP for JLC assembly and must still be sourced and fitted separately.

### 4. P2 — Silkscreen and regression expectations need reconciliation

The remaining **90 DRC warnings** comprise 39 silk-over-copper, 38 silk overlaps, one silk-edge clearance, ten footprint-library mismatches, one dangling +3V3 track, and one NRESET via connected on only one layer. They are not reported unrouted nets. The TP13 reference is clipped near the board edge; old M1/M2 legends remain near the former marker positions, whereas TP16/TP17 have moved to (79.29,55.15)/(77.96,55.15). Clean the labeling before generating assembly/probing instructions.

Of 17 selected hardware regression tests, 15 pass. The second failure is the SENSE routing-class test expecting 0.2 mm clearance while the project specifies 0.6 mm. A more conservative clearance is not an electrical defect; reconcile the intent and test rather than reducing clearance merely to pass it. Review intentional library differences before any library update.

## Unintended behaviors to qualify

### Probe protection is not yet coordinated with the IC limits

D10 connects directly to both shield outputs, without a series limiter. D8/D9 also clamp directly at the protected CIN nodes. The selected TVS typically breaks down at 6.4 V and has a 7 V typical TLP clamp at 1 A; it is not a precision 3.3 V clamp. These exceed the FDC analog-pin DC limits, especially with its supply off. R30/R31 limit electrode current but do not sit between the TVS node and CIN. This is an unresolved protection risk, not proof of a particular ESD failure. Review residual voltage/current at the IC and test both polarities, powered and unpowered, with the final coating. [TVS datasheet](https://www.ti.com/lit/ds/symlink/tpd1e01b04.pdf).

### A wet probe can saturate or settle poorly

Both 16 × 30 mm electrodes occupy all four layers; both outer faces sense the environment. A deliberately strong-coupling estimate for one electrode's two external faces, with grounded conductive material and coating εr=4, is about **136 pF at 0.25 mm coating**, or **68 pF at 0.50 mm**. These are screening calculations, not predictions for actual soil. The thinner example exceeds the approximate CAPDAC-plus-conversion range. The earlier front-only simulation cannot qualify this geometry.

With 5.1 kΩ input resistors, 100 pF gives RC=0.51 µs. That is not comfortably below TI's recommended sub-microsecond input settling scale. Sweep raw capacitance, CAPDAC headroom, noise and settling in wet/saline soil using the actual coating and insertion depth. Also check shield loading; the specified drive limit is 400 pF. Keep measurements single-ended: externally tied SHLD1/SHLD2 preclude differential operation. [FDC1004 datasheet](https://www.ti.com/lit/ds/symlink/fdc1004.pdf), [TI resistor guidance](https://e2e.ti.com/support/sensors-group/sensors/f/sensors-forum/527553/fdc1004-esd-protection).

### Powered-off FDC leakage remains unknown

SDA/SCL stay pulled up to the always-on rail while the FDC supply is discharged. Their independent 6 V absolute maximum does not guarantee negligible leakage at VDD=0. The old statement in HARDWARE.md that this proves no back-powering is too strong. Measure both off-rail voltage and battery current; active discharge can hide leakage by keeping the rail near zero while wasting current. Do not move the shared pull-ups onto the switched rail: that would prevent the PMIC from receiving the command to enable it. [FDC1004 ratings](https://www.ti.com/lit/ds/symlink/fdc1004.pdf).

### Radio supply and battery margins require real measurements

The BL54L15 receives VOUT directly. Ezurio specifies 10 mV maximum ripple/noise; Nordic lists 70 mVpp typical LP/ULP ripple. The real sensor application requests and verifies HP before sensing and radio, which is appropriate, but measure the rail at U1.26 during TX and supply transitions. [Ezurio supply requirements](https://www.ezurio.com/documentation/datasheet-bl54l10-and-bl54l15-series), [local Nordic datasheet, Table 10](../../doc/datasheets/nPM2100_Datasheet_v1.0.pdf).

C3+C25+C27 total 12.3 µF nominal directly on VOUT, plus the module's input capacitance. Verify 0.7–15 µF effective over bias/tolerance/temperature. C21/C23 now use the exact Nordic-reference GRM158R60J226ME01D part, but effective capacitance still matters. C26/C28 are on the separate VINT-fed LDOSW branch, not directly on VOUT; test their turn-on transient separately.

Use a depleted/cold-cell equivalent with realistic source resistance to test startup, repeated wake and TX. Keep the SHT45 heater disabled until the cell/load is qualified. Q1 correctly protects reverse insertion, but is not a fuse or a complete reverse-current barrier. J4.1 is directly connected to +3V3: use it as target-voltage reference, not as an unqualified external supply with a primary cell installed.

## Wiring that checked out

| Path | Current connections / conclusion |
|---|---|
| Battery and reverse PMOS | BT1.1 → Q1 drain 3; Q1 source 2 → VBAT; gate 1 → GND. Holder positive pad is the left contact per its archived drawing. |
| Boost power stage | L10 connects protected VBAT to U2.2 SW. U2.14/.15 share VINT with C23/C24. U2.13 supplies +3V3. No functional external load is wired directly to VINT; TP10 is measurement access. |
| PMIC defaults | VSET/SHPHLD/GPIO1 are unused; SYSGDEN is grounded. Cold boot requires software to select 3.3 V and load-switch mode before enabling FDC. |
| FDC power and inputs | U2.12 → U3.8; CIN1/.2 and CIN2/.3 have their separate series resistors/clamps. CIN3/4 are NC. GND is U3.7. |
| I²C | U1.28=P1.10 SDA; U1.35=P1.11 SCL; both reach PMIC/FDC/SHT with separate 4.7 kΩ pull-ups to +3V3. Firmware uses these pins at 100 kHz. Addresses 0x74/0x50/0x44 do not collide. |
| SHT45 | SDA1, SCL2, VDD3, GND4; main-rail supply and local C27. |
| Programming/reset | J4 pins 2/4/6 reach SWDIO/SWDCLK/SWO through 100 Ω; pin 10 reaches reset through R35 then R1. PMIC PG/RESET joins between those resistors; U1 reset is pin 7. J4 grounds are pins 3/5/9. |
| Crystal and markers | XL1 U1.25 → X1.1; XL2 U1.24 → X1.2. TP16 → U1.20 P1.07; TP17 → U1.21 P1.06. Marker nets are routed in this snapshot. |

ERC reports zero errors and ten symbol-library warnings. Native refilled DRC reports zero unconnected items and zero schematic-parity issues; its existing ignored categories are preserved in the report. The sensor host tests pass, and source inspection confirms real sensor reads, 3.3 V configuration, HP scheduling, shutdown and watchdog handling. This review did not rebuild the SDK image or exercise physical hardware.

## First-article checks after the layout corrections

1. Inspect final Gerber copper/mask/drill/paste layers and assembly rotations. Confirm U1 hand-fitting instructions, U2 exposed-pad paste/via treatment, BT1 polarity and all labeled test points.
2. Check unpowered rail resistance and battery polarity, then start with a current-limited battery-equivalent supply. Scope main and FDC rails through startup, shutdown and repeated wake cycles.
3. Measure sleep current, FDC-off leakage, I²C levels/rise time, radio ripple, and cold/depleted-cell behavior. Inject a stuck bus and verify the PMIC actually power-cycles the peripherals.
4. Measure crystal startup/frequency with the selected internal load setting. Test SWD attach/reset and use the correct sensor image; the older BTHome demo advertises simulated values.
5. Qualify coated-probe range, shield waveform, temperature drift, salinity, abrasion and water absorption; test ESD on the finished assembly. Keep coating off the SHT45 sensing membrane.
6. Verify the actual holder, installed cell, enclosure, screw and programming-cable clearances. The rendered holder is a visualization substitute and this render does not include the final enclosure. Test BLE performance with the closed enclosure and wet probe; footprint keepout compliance alone does not qualify the antenna.

The concrete fab-rule failures and return-layout regression should be resolved before a prototype order. Wet-soil, supply, leakage, ESD and RF measurements are first-article qualification work; until those pass, treat an order as an engineering prototype run rather than a production release.
