# Probe copper and CIN protection — 9 September 2026

Implemented in the maintained schematic and PCB. [Copper layers](layers.png) · [Protection schematic](protection.png).

## Changes

- D8 now connects CIN1_PROTECTED to GND; D9 connects CIN2_PROTECTED to GND. The signal path is electrode → R30/R31 → CIN pin, with the TVS shunting that protected node to ground. The previous electrode-side diode branches were removed and replaced with short 0.2 mm tracks to the protected resistor pads.
- The original diode positions and 0.5 mm ground connections to dedicated In1 return fingers are retained. Moving the diodes closer to U3 would overlap its assembly courtyard; the corrected routing provides the intended electrical placement without that overlap.
- Both 16 × 30 mm sense electrodes now occupy F.Cu, In1.Cu, In2.Cu and B.Cu. Four 0.6/0.3 mm through vias per electrode join all layers with solid zone connections. Sense copper occupies the former inner/back windows.
- SHLD already existed on all four layers. Its lower opening is now closed: each layer has a complete perimeter around the lower electrode, including a chamfered strip across its bottom. Three additional SHLD through vias stitch that strip. The sense-to-shield clearance remains 0.2 mm; copper-to-edge clearance remains 0.3 mm.
- Ground remains outside the active electrode region. No ground or SHLD backing plane is inserted between the stacked sense areas. Both outside faces intentionally sense the environment.

## Electrical review

TI's FDC1004 support guidance places optional series resistance between the electrode and the ESD device, with the clamp at the CIN side. It also calls for input RC much less than 1 µs. This supports the corrected topology, but does not qualify this particular diode/resistor combination. [TI FDC1004 ESD guidance](https://e2e.ti.com/support/sensors-group/sensors/f/sensors-forum/527553/fdc1004-esd-protection).

R30/R31 remain the existing 5.1 kohm parts. At 100 pF their RC is 0.51 µs, which is not comfortably much less than 1 µs. Their pulse survivability and conversion settling require measurement; changing their resistance without checking the clamp residual and pulse stress would not establish a qualified design. The selected TPD1E01B04's breakdown/clamp voltage exceeds the CIN DC pin limits. Moving it fixes the topology, not proof of ESD immunity. [TVS datasheet](https://www.ti.com/lit/ds/symlink/tpd1e01b04.pdf).

The buried sense copies do not provide four independent sensing surfaces. The principal change is adding the second external sensing face. Larger or closer guards also reduce useful fringe-field sensitivity, so the completed ring is deliberate boundary control rather than an assumed sensitivity increase. [TI sensor/shield geometry guidance, §7.2](https://www.ti.com/lit/an/snoa927a/snoa927a.pdf).

The FDC1004 has a ±15 pF conversion window around its selected offset, a CAPDAC setting up to approximately 96.9 pF, and a 400 pF specified shield load. Automatic CAPDAC changes can move the measurement window but cannot accommodate arbitrarily large total capacitance. Shared SHLD requires the existing single-ended measurement configuration. [FDC1004 datasheet](https://www.ti.com/lit/ds/symlink/fdc1004.pdf).

A deliberately strong-coupling estimate for the **two external faces of one electrode** is `C = ε0 εr (960 mm²) / coating thickness`. Assuming grounded conductive material against both faces and coating εr=4:

| Cured coating thickness | Approximate sense capacitance |
|---|---:|
| 0.10 mm | 340 pF |
| 0.25 mm | 136 pF |
| 0.50 mm | 68 pF |

These estimates omit fringe fields, feed traces, coating water uptake and the actual soil/body return impedance. They are not calibration predictions. They show why the earlier ≥0.25 mm coating target and front-only electrostatic simulation cannot qualify this revised geometry. At the first two thicknesses the strong-coupling estimate exceeds the available input range. Even 0.50 mm is not a validated coating specification. Prototype with the intended coating, soil salinity and insertion depth; measure raw capacitance, CAPDAC headroom, settling/noise and shield waveform/load. The above-soil electrode does not cancel soil conductivity or a different coating/environment around the buried electrode.

## Verification

- Native KiCad zone refill/save and schematic-parity DRC: **no physical-rule errors, no parity issues, 43 existing warnings, two existing unconnected items**. No rules or exclusions were changed. [DRC](drc.json).
- The existing missing connections are a GND-zone connection and TP17 `/MARK2` to U1 pad 30. They are unchanged by this work.
- Native ERC: **zero errors, 10 warnings**. [ERC](erc.json).
- Filled-polygon inspection confirms both sense nets and all four connecting vias per electrode on every copper layer. SHLD copper is present on all four sides of the lower electrode on every layer. Native copper and schematic renders were visually inspected.
- Existing tests: protection topology 4/4, ESD ground returns 1/1, routing rules 5/5. The diode-net expectations now match the corrected topology.
- Source hashes are in [source-sha256.json](source-sha256.json). Pre-change source copies and native layer exports are retained under `tmp/probe-review-2026-09-09/`.

This revision completes the requested layout changes. Wet-soil range and ESD bench qualification remain outstanding.
