> Subsequent status: schematic changes and Alex’s PCB update are complete; source files match the regenerated JLC quote package. See [Rev A checkpoint](rev-a-checkpoint/README.md). Earlier implementation-stage notes below are historical.

# Consolidated development-board BOM

Status: **implemented in the schematic only** at Alex’s request. PCB update and routing
are assigned to Alex. [Implementation and checks](schematic-consolidation-2026-09-09/README.md).
The rationale and original quote estimates below remain the design record; capacitor
qualification and a refreshed assembly quote are still pending.
Baseline: `f6205a2`. See [checkpoint tests](sweep-2026-09-09.md).

## Decision

Alex wants fewer unique capacitor and diode parts for these development boards.
Keep ESD suppressors fitted, consolidate all ten to one part, and accept reduced
power-rail clamping performance. This build is not an intensive ESD qualification
run. Select consolidated capacitors after checking effective capacitance and fit.
The development ESD tradeoff does not imply production qualification.

This is the most consolidated practical target identified using existing quoted
parts while preserving distinct circuit functions, not a proven global optimum
across all available parts. Seven capacitor SKUs become four; two diode SKUs
become one. Merge the 4.7 kΩ and 5.1 kΩ groups onto 4.7 kΩ, omit C13 and
bypass R1 with copper per the supplied module integration guidance.
JLC purchase lines drop from 20 to 14, Extended lines from 12 to eight.
U1 remains a separate manual-fit purchase: 15 unique parts for the complete
product, excluding the battery cell and mechanical enclosure.

## Proposed complete purchase list

| References | Qty/board | Value/function | Proposed MPN | LCSC | Quote library | Action |
| --- | ---: | --- | --- | --- | --- | --- |
| BT1 | 1 | CR2032 holder | CR2032-BS-6 | C22363833 | Extended | Retain |
| C3, C21, C23 | 3 | 10 µF, 25 V, X5R, 0603 | CL10A106MA8NRNC | C96446 | Basic | C21/C23 change from 22 µF 0402; qualify and check fit |
| C22, C24 | 2 | 1 nF, 50 V, X7R, 0402 | 0402B102K500NT | C1523 | Basic | Retain PMIC RF bypass |
| C25, C26 | 2 | 2.2 µF, 6.3 V, X5R, 0402 | CL05A225MQ5NSNC | C12530 | Basic | C26 changes from 1 µF; qualify |
| C27, C28 | 2 | 100 nF, 16 V, X7R, 0402 | CL05B104KO5NNNC | C1525 | Basic | Retain local bypass |
| D1–D10 | 10 | Bidirectional low-capacitance ESD, DPY | TPD1E01B04DPYR | C779389 | Extended | Change D1–D3; retain D4–D10 |
| L10 | 1 | 2.2 µH PMIC inductor | DFE201210U-2R2M=P2 | C2049745 | Extended | Retain |
| Q1 | 1 | Reverse-battery PMOS | DMG2305UX-13 | C144153 | Extended | Retain |
| R22, R23, R30, R31, R36, R37 | 6 | 4.7 kΩ, 0402 | 0402WGF4701TCE | C25900 | Basic | Retain pull-ups; change R30/R31 from 5.1 kΩ |
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
- **Keep 1 nF and 100 nF separate:** PMIC RF bypass and local bypass
  functions differ. C13 is now proposed for omission per the module review below. Making dielectric labels identical
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
| R30/R31 to common 4.7 kΩ | $0.026 − 10 × $0.0029 | −$0.0030 | $0 | −$0.0030 |
| Omit C13 | Eliminate quoted 20-piece purchase | $0.0700 | $3.07 | $3.1400 |
| Remove R1 and bridge with copper | Eliminate five-piece purchase | $0.0195 | $0 | $0.0195 |
| Combined | | $4.2392 | $12.28 | **$16.5192** |

C26's original purchase is 20 pieces for five fitted capacitors. Original diode
purchases are 17 + 39 = 56 for 50 fitted parts. The common-diode estimate assumes
55 purchased pieces including allowance; with 56, combined savings are $16.4467.
Re-quote for actual attrition quantities, MOQs and price tiers.

New components: approximately $50.9860. New Extended fees: $24.56. New displayed
PCB + PCBA total: **$117.61**, saving **$16.52/order**, **$3.30/board**, about
**12.3%**. Checkout rounding can move cents. This excludes unshown shipping,
tax, manual module purchases, battery and enclosure costs.

Other scenarios discussed: C25/C26 plus common low-capacitance diodes alone saves
$8.17. Adding the 10 µF consolidation saves another $5.19. Using the stronger
diode everywhere saves about $2.55 instead of $3.41 and changes sensing loading.
Replacing C3 with existing 22 µF costs about $1.06 extra with no feeder-fee saving.

## Common 4.7 kΩ resistors

Propose **0402WGF4701TCE / C25900** for all six R22/R23/R30/R31/R36/R37.
Retain the four existing I²C pull-ups and change only the two sense series
resistors from 5.1 kΩ to 4.7 kΩ. Their package and 1% tolerance stay the same.

This lowers sense series resistance by 7.84%. At an illustrative 100 pF load,
RC changes from 0.51 µs to 0.47 µs, modestly improving settling. For the same
voltage across the resistor, current rises by 8.51%; this is a simple Ohm's-law
comparison, not a prediction of ESD current with a nonlinear clamp. Neither value
establishes pulse survival or measurement settling by itself. The development
tradeoff is reasonable and aligns with retaining basic ESD protection while
prioritizing sensing and a simpler BOM. Check sensor repeatability after the change.

Both resistor lines are Basic. The supplied quote charges $0.058 for 20 of the
4.7 kΩ part ($0.0029 each) and $0.026 for ten of the 5.1 kΩ part ($0.0026 each).
At unchanged unit prices, consolidating onto 4.7 kΩ raises the five-board parts
cost by $0.003, effectively zero, and saves no feeder fee. Its benefit is one
fewer SKU. A refreshed quote might change the combined-quantity price tier.

Using 5.1 kΩ everywhere instead would save $0.006 at these prices but weaken the
I²C pull-ups (roughly 8.5% longer RC rise time at fixed bus capacitance). Prefer
4.7 kΩ to preserve the reviewed bus pull-ups and slightly reduce sense settling
resistance. Retain the 100 Ω debug group. R1 is now proposed for removal and a copper
bridge, as explained in the module-datasheet review below.

Source topology and existing settling limitations: [probe review](probe-review-2026-09-09/README.md).
The quoted resistor inputs are rows 19–20 in the archived source data. The current
TI support link returned HTTP 403 during this follow-up; no new manufacturer
approval of either value is claimed.

## R1 and C13: original screening, superseded by supplied module datasheet

Alex asked whether R1 could join the 4.7 kΩ group and C13 could join another
capacitor group. Review found a functional reason not to adopt either as a
routine BOM substitution. The initial proposal retained R1 = 1 kΩ and C13 = 3.9 pF. The later module
datasheet review below supersedes that decision and the purchase table is updated.

The maintained netlist is programmer RESET_EXT → R35 (100 Ω) → SWD_RST →
R1 (1 kΩ) → module NRESET. PMIC PG/RESET also connects to SWD_RST; C13
shunts NRESET to GND. R1 is a series resistor, not a pull-up. Ezurio specifies
a 13 kΩ internal reset pull-up in BL54L15.

With an ideal zero-volt programmer output, ignoring the PMIC pull-up and other
nonidealities, the nominal module reset level is approximately:

- Existing: VDD × 1.1 kΩ / (13 kΩ + 1.1 kΩ) = 0.078 VDD, or 0.26 V at 3.3 V.
- Proposed R1 = 4.7 kΩ: VDD × 4.8 kΩ / (13 kΩ + 4.8 kΩ) = 0.270 VDD,
  or 0.89 V at 3.3 V.

These are screening calculations, not guaranteed reset thresholds or a worst-case
model. Pull-up tolerance, reset input threshold, programmer/PMIC output-low voltage,
PMIC pull-up and module internal circuitry must be included before approving
4.7 kΩ. The substantial reduction in low-level margin makes it a poor automatic
substitution. It would save only $0.005 per five-board order at the quoted prices
($0.0195 old R1 purchase minus five × $0.0029), with no Extended fee saving.

Nordic explicitly identifies the 1 kΩ / 3.9 pF QFN reset network as suppression
of TX second-harmonic emissions coupled onto RESET. The RF fundamental is around
2.4 GHz; the second harmonic is around 4.8 GHz. At these frequencies capacitor
ESL, self-resonance, package and layout matter; more nominal capacitance does not
mean more suppression. Nordic specifically rejects replacing 3.9 pF with 10 nF.
The ideal RC corner (~41 MHz for 1 kΩ and 3.9 pF) alone does not explain or
validate the GHz behavior. C13 is neither a crystal load capacitor nor a generic
reset-delay capacitor.

Our board uses an Ezurio module rather than a bare QFN reference design. The
Nordic evidence explains the inherited values but does not prove an additional
host-side C13 is required if the module already provides the relevant internal
filtering. Confirm that with Ezurio/module circuit evidence before removing the
host capacitor or replacing it with 1 nF. Current module documentation inspected
here does not establish the internal filtering implementation. Do not claim this
host layout is RF-qualified merely because the nominal values match Nordic's.

Replacing C13 with the existing 1 nF part would theoretically save $3.11/order
($0.07 old purchase plus $3.07 fee minus five × $0.006), and omitting it would
save $3.14. At this stage these were unapproved scenarios. The later module-specific
review below now includes omission (not a larger capacitor) in target totals.
The dev decision to accept weaker ESD protection does not automatically accept
changed reset reliability or radio-emission behavior. The initial recommendation was to keep the pair pending module-specific evidence;
that evidence is evaluated below.

Sources: [Ezurio reset pull-up and integration documentation](https://www.ezurio.com/documentation/datasheet-bl54l10-and-bl54l15-series),
[Nordic explanation and rejection of 10 nF substitution](https://devzone.nordicsemi.com/f/nordic-q-a/121811/nrf54lxx---reset-circuitry),
[Nordic confirmation of the tested 1 kΩ / 3.9 pF network](https://devzone.nordicsemi.com/f/nordic-q-a/127632/nrf54l15-reference-design-onboarding-questions/564599).

## Supplied BL54L15 datasheet review: omit the external reset RC

Source: user-supplied `453-00001R_new.pdf`, BL54L15/BL54L10 Series v1.8,
42 pages. Text searched across the document; pages 9, 20 and 21 visually inspected.
Source SHA-256: `1968a812ea2bd265636c7432667eabbafa98503b96df2c7493b6a96265f017b6`.

Section 7.1, printed page 20, identifies one mandatory external 10 µF capacitor
for module integration. Its reset bullet says to wire nRESET to a push button
or drive it from the host. The continuation on page 21 identifies the internal
13 kΩ pull-up. No external series resistor or reset shunt capacitor is specified.
The block diagram on page 9 is functional, not an internal passive schematic;
it does not establish whether the exact Nordic 1 kΩ / 3.9 pF pair exists inside.

**Revised development recommendation: omit C13 and remove/bypass R1 using copper.**
This follows the module integration guidance instead of imposing the bare-SoC
reference RC on the carrier. Do not replace R1 with 4.7 kΩ or C13 with a much
larger capacitor. R1 is in series: simply marking it DNP without bridging it
would disconnect reset and is incorrect. Retain R35 (100 Ω), D7, and the existing
PMIC PG/RESET connection. The remaining 100 Ω debug resistor is our carrier
protection choice, not an Ezurio requirement.

This is a module-specific engineering inference from its documented integration
requirements, not proof of the internal filter implementation or RF/ESD testing
of this carrier. Verify programming, connect-under-reset, PMIC-triggered reset,
power-up and normal radio operation on the development boards. The earlier
voltage-divider objection still applies to adding 4.7 kΩ in series; removing
R1 avoids that objection instead of trying to tolerate the larger voltage drop.

Omission saves $3.14 for C13 and $0.0195 for R1 in the five-board quote; reduced
placement charges, if any, are not included. The target is now four capacitor
SKUs and two resistor SKUs (4.7 kΩ and 100 Ω), with one diode SKU. Total: 14 JLC
purchase lines, eight Extended lines, plus the required manual-fit module.
No schematic or PCB edits were made during this document review.

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
With all capacitor/diode proposals, this illustrative scenario totals **$114.34**,
or **$19.79/order ($3.96/board)** saved. Keep the quote-backed capacitor/diode
estimate above separate from this conditional sensor-price estimate. Ordering
directly from LCSC for hand assembly also has separate shipping/procurement costs.

Sources: [Sensirion SHT4x datasheet, sections 5, 6, 9 and 10](https://sensirion.com/resource/datasheet/sht4x),
[JLC C2909890 listing](https://jlcpcb.com/partdetail/Sensirion-SHT40_AD1BR2/C2909890),
[LCSC part link](https://www.lcsc.com/product-detail/C2909890.html).
The JLC page confirms MPN, manufacturer, assembly compatibility and Extended type;
price above comes from PCBParts, not from a completed quote.

## Next steps

1. Validate capacitor bias/corner behavior and 0603 fit; record final MPNs or fallbacks.
2. Implement common diodes, common 4.7 kΩ resistors and accepted capacitor changes
   in schematic and PCB. Omit C13 and remove R1 with a copper bridge, retaining
   R35/D7 and the PMIC reset connection; verify both reset sources on hardware.
3. Update intentional selection checks only after review: `test_reservoir_selection.py`
   currently enforces Nordic-listed 0402 parts. Do not bypass it merely to pass a test.
4. Reconcile the three checkpoint failures; run connectivity, ERC/DRC and repository
   checks; regenerate JLC BOM/CPL and obtain an updated quote.
5. Check cold/aged-cell startup, radio droop, FDC power-up and sensing repeatability
   on prototypes. Intensive ESD qualification remains a separate production task.
