# Cost reduction — 9 September 2026

The user accepted SHT40 as the reference sensor and requested implementation
of the cost recommendations. The starting ten-board quote is $33.00 PCB plus
$191.37 assembly = $224.37, excluding BLE, shipping and tax. Components are
$138.55 and Extended feeder fees are $39.91.

## Implemented selections

| Ref | Previous | Selected | Reason |
| --- | --- | --- | --- |
| Q1 | DMG2305UX-7 / C150470 | Diodes DMG2305UX-13 / C144153 | Same device and SOT-23 footprint; 10,000-piece reel instead of 3,000-piece reel. JLC purchases individual quantities. |
| U4 | SHT45-AD1F-R2 / C5360602 | Sensirion SHT40-AD1F-R2 / C7461846 | Lower accuracy accepted for reference use; retains integrated membrane, 0x44 address, pinout and footprint. |
| C3 | CL10X106MO8NRNC / C3039688 | Samsung CL10A106MA8NRNC / C96446 | Basic part removes one feeder fee; retains nominal 10 µF and 0603 footprint. |
| R22/R23/R36/R37 | Two different value strings, same C25900 | Common value `4.7k 1%`, same C25900 | One unambiguous BOM row with all four references. Supply nets remain separate. |

Values, MPNs and LCSC fields are synchronized in the schematic and PCB.
The export now labels the procurement column `JLCPCB Part #` to avoid relying
on automatic matching. All 38 JLC-fitted references are present in 20 BOM rows.
U1 remains DNP for separate BLE-module fitting. BT1 remains factory assembled.

## Electrical and mechanical checks

**Q1:** The [Diodes ordering table](https://www.diodes.com/datasheet/download/DMG2305UX.pdf)
lists both suffixes against the same electrical specifications and package.
The existing reverse-battery topology and low-voltage RDS(on) rating remain.

**U4:** [Sensirion SHT4x v7.3](https://sensirion.com/resource/datasheet/sht4x)
gives SDA=1, SCL=2, VDD=3, VSS=4 for both accuracy variants. The membrane
package and land pattern are shared. The existing SHT45-named STEP model
is retained as the same package geometry, not a new procurement selection.
The no-central-pad footprint, copper keepout and assembly orientation stay intact.
The current datasheet describes the filter as polyimide; older product pages
call it PTFE. Select the exact Sensirion AD1F ordering code in either case.

Typical reference accuracy becomes ±0.2 °C / ±1.8 %RH under the specified
conditions. If using the earlier illustrative 20–60 fF/°C soil coefficient,
temperature-sensor uncertainty becomes 4–12 fF, versus 2–6 fF with SHT45.
This is not a calibrated system specification. Ambient-to-soil temperature
differences and enclosure effects must be assessed on the prototype.
The existing firmware uses 0x44, command 0xFD, a 10 ms wait and the common
SHT4x CRC/conversion algorithm. No firmware protocol change is required.

**C3:** The [Samsung part page](https://product.samsungsem.com/mlcc/CL10A106MA8NRN.do)
identifies CL10A106MA8NRNC as 10 µF, ±20%, 25 V, 0603, X5R (−55…+85 °C).
The higher voltage rating alone is not evidence of better capacitance retention.
The exact manufacturer DC-bias curve was extracted and interpolated:

| Part | Typical capacitance at 3.0 V | At 3.3 V | At 3.6 V |
| --- | ---: | ---: | ---: |
| New C3, CL10A106MA8NRNC | 7.01 µF | 6.60 µF | 6.21 µF |

Previous C3 is approximately 6.85 µF at 3.3 V, so the new part has about
3.6% less typical capacitance at this operating point. The nominal value stays
10 µF as required by the module design. Applying −20% tolerance and −15%
temperature factors to the new part's typical 3.3 V curve gives an illustrative
4.49 µF; this is a screening estimate, not a guaranteed combined corner or
an aging-qualified lower bound. Other retained X5R parts already have an
85 °C limit. Existing module transient/ripple and PMIC total effective
0.7–15 µF output-capacitance qualification is still open; this substitution
does not establish that the entire board is qualified.

**C26 retained:** Samsung CL05A105KA5NQNC / C52923 was screened, not fitted.
Its [manufacturer curve](https://product.samsungsem.com/mlcc/CL05A105KA5NQN.do)
shows 0.576 µF typical at 3.3 V before tolerance, temperature and aging.
TI's [FDC1004 example](https://www.ti.com/lit/ds/symlink/fdc1004.pdf) pairs a
1 µF tantalum with 100 nF ceramic. This cheap candidate is not a verified
equivalent to that reservoir, so retain the existing GRM155Z71A105KE01D and
C28. This does not claim that the old capacitor has been newly qualified.
C21/C23, the inductor, crystal, and protection components are otherwise retained.

Manufacturer page HTML and extracted curve data are saved in `sources/`.
These curves are typical reference data, not production limits.

## Price estimate

Database pricing at the ten-piece tier is $6.1227 → $2.1950 per sensor and
$0.6606 → $0.3613 per Q1. C3 below 100/200 pieces is $0.1034 → $0.0552.
Using ten charged pieces of each, the component reduction is $42.752 and
one removed feeder fee adds $3.07, for approximately $45.82 saved.
Applying that delta to the user's quote gives **about $178.55 total,
$17.85 per board**, before BLE, shipping and tax. This is a comparative
estimate; actual charged quantities, attrition, price tiers and stock can
change the checkout result. Requote the exported BOM. Expected Extended
types fall from 13 to 12, with fees $39.91 → $36.84 at $3.07/type.

## Verification

- Exported netlists have identical net names and reference/pin memberships.
- Only seven footprint property blocks changed. All pads, copper, routing,
  placement, keepouts, zones, footprints and 3D transforms are preserved.
- ERC is unchanged: zero errors, 11 existing warnings.
- DRC has the same rule/severity/item identities: 38 existing warnings,
  two previously accepted +3V3-via keepout errors, zero unconnected items
  and zero schematic-parity issues. The existing export gate accepts only
  those exact two vias; no exceptions were added.
- Four existing BOM/export unit tests passed.
- Sensor host tests passed: measurements, CRC, range, bounded waits and
  bus-fault cleanup. This is not hardware validation or a new SDK build.
- Rendered schematic checked for legible changed values and unchanged wiring.

## Quote files

Use the coherent package in `production/jlc-cost-reduced/`:
`JLC-BOM.csv`, `JLC-CPL.csv`, and `JLC-Gerbers.zip`.
The PCB geometry is unchanged; this package regenerates all three from the
same sources. `Product-BOM.csv`, `schematic.pdf`, source hashes and check
reports are included. No order was submitted.
