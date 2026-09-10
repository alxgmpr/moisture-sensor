# Consolidated development-board BOM

Status: selected direction for the next revision, **not implemented in KiCad**.
Baseline: `f6205a2`. See [checkpoint tests](sweep-2026-09-09.md).

## Decision

Alex wants fewer unique capacitor and diode parts for these development boards.
Keep ESD suppressors fitted, consolidate all ten to one part, and accept reduced
power-rail clamping performance. This build is not an intensive ESD qualification
run. Select consolidated capacitors after checking effective capacitance and fit.
The development ESD tradeoff does not imply production qualification.

This is the most consolidated practical target identified using existing quoted
parts while preserving distinct circuit functions, not a proven global optimum
across all available parts. Seven capacitor SKUs become five; two diode SKUs
become one. JLC purchase lines drop from 20 to 17, Extended lines from 12 to nine.
U1 remains a separate manual-fit purchase: 18 unique parts for the complete
product, excluding the battery cell and mechanical enclosure.

## Proposed complete purchase list

| References | Qty/board | Value/function | Proposed MPN | LCSC | Quote library | Action |
| --- | ---: | --- | --- | --- | --- | --- |
| BT1 | 1 | CR2032 holder | CR2032-BS-6 | C22363833 | Extended | Retain |
| C3, C21, C23 | 3 | 10 µF, 25 V, X5R, 0603 | CL10A106MA8NRNC | C96446 | Basic | C21/C23 change from 22 µF 0402; qualify and check fit |
| C13 | 1 | 3.9 pF, C0G, 0402 | 0402CG3R9C500NT | C1566 | Extended | Retain reset RF filter |
| C22, C24 | 2 | 1 nF, 50 V, X7R, 0402 | 0402B102K500NT | C1523 | Basic | Retain PMIC RF bypass |
| C25, C26 | 2 | 2.2 µF, 6.3 V, X5R, 0402 | CL05A225MQ5NSNC | C12530 | Basic | C26 changes from 1 µF; qualify |
| C27, C28 | 2 | 100 nF, 16 V, X7R, 0402 | CL05B104KO5NNNC | C1525 | Basic | Retain local bypass |
| D1–D10 | 10 | Bidirectional low-capacitance ESD, DPY | TPD1E01B04DPYR | C779389 | Extended | Change D1–D3; retain D4–D10 |
| L10 | 1 | 2.2 µH PMIC inductor | DFE201210U-2R2M=P2 | C2049745 | Extended | Retain |
| Q1 | 1 | Reverse-battery PMOS | DMG2305UX-13 | C144153 | Extended | Retain |
| R1 | 1 | 1 kΩ, 0402 | 0402WGF1001TCE | C11702 | Basic | Retain reset filtering |
| R22, R23, R36, R37 | 4 | 4.7 kΩ, 0402 | 0402WGF4701TCE | C25900 | Basic | Retain I²C pull-ups |
| R30, R31 | 2 | 5.1 kΩ, 0402 | 0402WGF5101TCE | C25905 | Basic | Retain sense series resistance |
| R32–R35 | 4 | 100 Ω, 0402 | 0402WGF1000TCE | C25076 | Basic | Retain debug series resistance |
| U2 | 1 | PMIC | NPM2100-QEAA-R7 | C46968654 | Extended | Retain |
| U3 | 1 | Capacitance converter | FDC1004DGSR | C2865994 | Extended | Retain |
| U4 | 1 | RH/T sensor, no integrated membrane | SHT40-AD1B-R2 | C2909890 | Extended | Dev cost option; retain AD1F if membrane protection is needed |
| X1 | 1 | 32.768 kHz, CL 7 pF crystal | CM8V-T1A-32.768KHZ-7PF-20PPM-TA-QC | C5136974 | Extended | Retain |
| U1 | 1 | BL54L15, manually fitted | 453-00001R | — | Outside JLC quote | Required in finished product |

This planning table is not the manufacturing BOM. The schematic fields remain
authoritative; regenerate BOM/CPL after implementing the revision.

## Why combining the diodes is reasonable here

Both existing MPNs are bidirectional and share the DPY footprint. There is no
unidirectional/bidirectional mix to resolve. Bidirectional D1 avoids a forward
shunt across a reversed raw battery; Q1 provides reverse-battery isolation.

Choose **TPD1E01B04DPYR at all ten locations**. It preserves the current sensing
and shield loading. Its DPY capacitance is 0.20 pF typical, 0.23 pF maximum;
the often-quoted 0.18 pF typical figure is for DPL. Its leakage maximum is 10 nA
at ±2.5 V. TPD1E1B04 instead has 1 pF typical capacitance and a 100 nA leakage
maximum at that bias. Using the stronger part everywhere changes the sensitive
nodes and is less attractive for a sensing development board.

The tradeoff is at D1/D2/D3: the common low-capacitance part clamps at 9.2 V
at 5 A TLP versus 6.8 V for the former rail part; the 8/20 µs surge-current
rating is 2.5 A versus 6.3 A. These are device test conditions, not guaranteed
voltages at the IC pins. Both have ±3.6 V standoff; that is not their clamping
voltage. Neither supplies sustained-overvoltage protection.

This is an acceptable development tradeoff, not a polarity incompatibility or
removal of all ESD protection. Survival of a particular discharge is unproven.
Consolidation also does not fix the existing D8 ground-via test failure.

Sources: [TPD1E01B04](https://www.ti.com/lit/ds/symlink/tpd1e01b04.pdf),
[TPD1E1B04](https://www.ti.com/lit/ds/symlink/tpd1e1b04.pdf).

## Capacitor checks before implementation

- **C21/C23 to common 10 µF:** each needs at least 3.5 µF effective over actual
  VBAT/VINT bias, tolerance, temperature and aging. Prior C3 screening found
  6.60 µF typical at 3.3 V and an illustrative 4.49 µF after tolerance and
  temperature factors. These are not guaranteed combined corners. Check VINT
  in every relevant mode, startup and transient droop. The change grows both
  footprints from 0402 to 0603; review physical fit and decoupling return loops.
- **C26 to common 2.2 µF:** verify C25's part at 3.3 V and the FDC switched-rail
  startup/supply behavior. TI's example uses a 1 µF tantalum plus 100 nF ceramic;
  nominal 2.2 µF ceramic alone does not establish equivalence. Retain C28.
  C26/C28 draw from the VINT-derived switched rail, not directly from VOUT.
- **Keep C3 at 10 µF:** moving it to the existing 22 µF part saves no Extended
  fee and increases cost. Any alternative must meet the 0.7–15 µF effective
  total VOUT limit including C3/C25/C27 and the module. Nominal 22 µF alone
  neither proves nor disproves compliance.
- **Keep 3.9 pF, 1 nF and 100 nF separate:** their reset RF filtering, PMIC RF
  bypass and local bypass functions differ. Making dielectric labels identical
  would not combine different-value SKUs. Moving the 2.2 µF roles to common
  10 µF could be studied separately, but changes output loading, area and inrush;
  it is not an established substitution in this target.

Sources: [prior Samsung curve screening](cost-reduction-2026-09-09/README.md),
[Nordic circuitry](https://docs.nordicsemi.com/r/bundle/ps_npm2100/page/chapters/hw_layout/ref_circuitry/doc/frontpage.html),
[Nordic hardware guidelines](https://docs.nordicsemi.com/r/bundle/nwp_058/),
[FDC1004 datasheet](https://www.ti.com/lit/ds/symlink/fdc1004.pdf).

## Five-board quote and savings

Source: supplied `JLC-BOM-JLCPCB Assembly Order (2).xls`, sheet
`JLCPCB BOM Tool - BOM Matching`, download time printed as 2026-09-10 09:32:38.
The file contains OOXML despite its extension. Screenshot charges: PCB $30.04,
PCBA $104.09, displayed total $134.13. Components sum to $55.2252, matching the
displayed $55.23. See [archived quote inputs](dev-bom-quote-inputs.json) for source
hashes, row numbers, quoted prices, library types and screenshot charges.

Twelve Extended lines and a $36.84 fee imply $3.07 per line. That is an inferred
uniform fee for this order, not a general JLC pricing rule. Library status and
unit prices are quote-specific. Hold the other displayed charges constant.

| Change | Component calculation | Parts savings | Fee savings | Order savings |
| --- | --- | ---: | ---: | ---: |
| C21/C23 to C3 part | $2.676 − 10 × $0.0552 | $2.1240 | $3.07 | $5.1940 |
| C26 to C25 part | $1.720 − 5 × $0.0058 | $1.6910 | $3.07 | $4.7610 |
| All diodes to TPD1E01B04 | $1.4977 + $2.8275 − 55 × $0.0725 | $0.3377 | $3.07 | $3.4077 |
| Combined | | $4.1527 | $9.21 | **$13.3627** |

C26's original purchase is 20 pieces for five fitted capacitors. Original diode
purchases are 17 + 39 = 56 for 50 fitted parts. The common-diode estimate assumes
55 purchased pieces including allowance; with 56, combined savings are $13.2902.
Re-quote for actual attrition quantities, MOQs and price tiers.

New components: approximately $51.0725. New Extended fees: $27.63. New displayed
PCB + PCBA total: **$120.77**, saving **$13.36/order**, **$2.67/board**, about
**10.0%**. Checkout rounding can move cents. This excludes unshown shipping,
tax, manual module purchases, battery and enclosure costs.

Other scenarios discussed: C25/C26 plus common low-capacitance diodes alone saves
$8.17. Adding the 10 µF consolidation saves another $5.19. Using the stronger
diode everywhere saves about $2.55 instead of $3.41 and changes sensing loading.
Replacing C3 with existing 22 µF costs about $1.06 extra with no feeder-fee saving.

## Additional U4 cost option requested during review

Use genuine **Sensirion SHT40-AD1B-R2, C2909890** as the proposed clean-bench
development option. Current KiCad remains SHT40-AD1F-R2, C7461846. This is a
unit-cost substitution, not a further reduction in unique parts or feeder fees.
Both options are Extended in the available data.

The AD1B retains the SHT40 accuracy class, 0x44 I²C address, commands, supply
range and four-pin assignment. Its 1.5 × 1.5 mm body uses the same recommended
land pattern, with a lower body height because it lacks the membrane. Existing
firmware needs no protocol change. Retain the no-central-pad footprint: the
distributor's DFN-4-EP label is not an instruction to solder the die pad.
Sensirion advises against soldering that pad or exposing copper underneath it.

The tradeoff is loss of the AD1F integrated protective membrane. AD1B is reasonable
for clean bench development; retain AD1F or provide suitable breathable external
protection for exposure to soil, dust or splashes. Keep the humidity opening free
of coating and assembly contamination. Earlier project notes preferred retaining
the membrane; this newly requested dev option is explicitly an exception under
consideration, not an unnoticed equivalent substitution.

Sensirion datasheet v7.3 (June 2026) calls the membrane polyimide; the catalog page
and older revisions call it PTFE. The functional distinction here is the presence
or absence of an integrated membrane, irrespective of that naming discrepancy.

PCBParts `jlc_get_part(mpn="SHT40-AD1B-R2")` returned genuine Sensirion C2909890,
Extended, database price $1.9053, stock 22,892. These are cached database values;
the quantity tier was not established and no live checkout price was available.
The current quoted AD1F is $12.80 for five, or $2.56 each. **If five AD1B parts
price at $1.9053 with no additional procurement fees**, the saving is
5 × ($2.56 − $1.9053) = **$3.2735**. There is no additional feeder-fee saving.
With all capacitor/diode proposals, this illustrative scenario totals **$117.49**,
or **$16.64/order ($3.33/board)** saved. Keep the quote-backed capacitor/diode
estimate above separate from this conditional sensor-price estimate. Ordering
directly from LCSC for hand assembly also has separate shipping/procurement costs.

Sources: [Sensirion SHT4x datasheet, sections 5, 6, 9 and 10](https://sensirion.com/resource/datasheet/sht4x),
[JLC C2909890 listing](https://jlcpcb.com/partdetail/Sensirion-SHT40_AD1BR2/C2909890),
[LCSC part link](https://www.lcsc.com/product-detail/C2909890.html).
The JLC page confirms MPN, manufacturer, assembly compatibility and Extended type;
price above comes from PCBParts, not from a completed quote.

## Next steps

1. Validate capacitor bias/corner behavior and 0603 fit; record final MPNs or fallbacks.
2. Implement common diodes and accepted capacitor changes in schematic and PCB.
3. Update intentional selection checks only after review: `test_reservoir_selection.py`
   currently enforces Nordic-listed 0402 parts. Do not bypass it merely to pass a test.
4. Reconcile the three checkpoint failures; run connectivity, ERC/DRC and repository
   checks; regenerate JLC BOM/CPL and obtain an updated quote.
5. Check cold/aged-cell startup, radio droop, FDC power-up and sensing repeatability
   on prototypes. Intensive ESD qualification remains a separate production task.
