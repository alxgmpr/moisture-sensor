# Footprint review — 9 September 2026

**The selected packages match the specified parts, but the placed footprints are not fully consistent. Correct the five rotated capacitor pad pairs and resolve the two existing keepout errors before releasing fabrication files.** This review did not edit the PCB, schematic, libraries, or manufacturing outputs.

Reviewed the maintained `nrf-moisture-sensor` PCB and schematic, not historical copies. Source hashes are in [source-sha256.json](source-sha256.json). There are 39 purchased components with 21 distinct MPNs. All 20 distinct LCSC selections resolve to the specified MPN and expected package family; U1 is the separately sourced Ezurio module. PCB and schematic Value, MPN, and LCSC fields agree. Fresh KiCad DRC reports zero schematic parity issues and zero unconnected items.

## Findings

1. **C21, C22, C23, C24, C27 have nonstandard pad orientation.** Their footprints are rotated ±90°, but their individual rectangular pads retain 0°/360° board orientation. After removing footprint rotation, both pads are 90° away from the library pattern. Relative to the component axis, the actual lands are 0.62 × 0.56 mm instead of 0.56 × 0.62 mm, with the same 0.96 mm center spacing. The gap becomes 0.34 mm instead of 0.40 mm. This is a small land-pattern error, not a wrong-size component selection or evidence of inevitable assembly failure. Restore the library pad orientation while preserving pad centers and nets, then refill and check routing. [Measured pad differences](pad-differences.json).

2. **Standard and hand-solder 0402 variants are mixed.** C26 uses enlarged capacitor lands, and R22/R23/R36/R37 use enlarged resistor lands. These remain compatible with their selected 0402 parts. For this reflow assembly, standardizing each passive family is reasonable, but the hand-solder variants alone are not a fabrication blocker. Replacement changes pad centers as well as outer pad edges, so check trace attachment afterward. Do not make resistor, capacitor, and diode land patterns identical merely because each is described as “0402.”

3. **Two +3V3 vias violate an existing no-via corridor.** Coordinates are (74.475, 72.675) and (74.350, 83.640) mm. Both lie in the long, unnamed no-via rule area between the module supply routing and PMIC region; these are not antenna-keepout errors. Resolve the routing/rule-area intent before fab rather than accepting an unexplained DRC failure. [Current DRC](drc.json).

4. **Hardware prose names obsolete purchases.** HARDWARE.md still describes C22/C24 as 0201 X5R, although the maintained schematic/BOM use 0402 X7R. It also still names the MPD BU2032SM-BT-GTR holder, whereas the selected part and actual footprint are Lian Xin CR2032-BS-6/C22363833. Use the maintained schematic-derived MPNs for purchasing; the holders are not interchangeable land patterns.

## Passive consistency

All dimensions below are mm; land size is along/across the component axis for the intended library orientation.

| Family | References | Intended individual land | Center spacing | Assessment |
|---|---|---|---|---|
| Standard 0402 capacitor | C13, C21–C25, C27, C28 | 0.56 × 0.62 | 0.96 | Five rotated-pad exceptions listed above; C13/C25/C28 match |
| Hand-solder 0402 capacitor | C26 | 0.735 × 0.62 | 1.135 | Compatible, larger land variant |
| Standard 0603 capacitor | C3 | 0.90 × 0.95 | 1.55 | Correct for CL10X106MO8NRNC |
| Standard 0402 resistor | R1, R30–R35 | 0.54 × 0.64 | 1.02 | Consistent |
| Hand-solder 0402 resistor | R22, R23, R36, R37 | 0.715 × 0.64 | 1.195 | Consistent within this group |
| TI DPY0002A protection diode | D1–D10 | 0.30 × 0.50 | 0.70 | All identical and correctly oriented |

C21/C23 are both GRM158R60J226ME01D, 22 µF/6.3 V X5R in 0402. The distributor package lookup confirms that selection; neither requires a larger nominal package footprint. Effective capacitance qualification remains a separate electrical requirement already documented in BOM.md.

## Package-specific checks

| Part | Assessment |
|---|---|
| U1, 453-00001R BL54L15 | Correct custom 39-land, 14 × 10 mm module footprint; placed pad geometry agrees with the project library. Existing module geometry/pin-assignment tests pass. Preserve the separate manual assembly stage; U1 is DNP only for JLC assembly. [Ezurio land-pattern and ordering documentation](https://www.ezurio.com/documentation/datasheet-bl54l10-and-bl54l15-series). |
| U2, NPM2100-QEAA-R7 | Correct QFN16 4 × 4 mm, 0.65 mm pitch; 2.7 × 2.7 mm ground land is compatible with the nominal 2.65 mm exposed package pad. Actual pad geometry matches the chosen KiCad footprint. Nine 0.20 mm drilled thermal pads remain inside the exposed land. Specify an assembly-compatible via treatment/stencil process; the footprint alone does not establish filled/capped vias. The TI-named 3D model is a generic visualization model. [Nordic package drawing](https://devzone.nordicsemi.com/cfs-file/__key/communityserver-discussions-components-files/4/nPM2100_2D00_Preliminary_5F00_Datasheet_5F00_v0.6.pdf). |
| U3, FDC1004DGSR | Correct MSOP/VSSOP DGS package, 10 pins, 3 × 3 mm body, 0.5 mm pitch; not the WSON variant. KiCad's 1.50 × 0.35 mm lands are slightly larger than TI's 1.45 × 0.30 mm example, with compatible pitch and lead placement. [TI datasheet, DGS drawing](https://www.ti.com/lit/ds/symlink/fdc1004.pdf). |
| U4, SHT45-AD1F-R2 | Correct 1.5 × 1.5 mm DFN4, 0.8 mm pitch, no central solder pad. Pads match the library; SDA/SCL/VDD/GND numbering agrees. No central exposed pad is appropriate for the heater. [Local manufacturer datasheet, §5.3](../../doc/datasheets/sensirion-sht45/HT_DS_Datasheet_SHT4x_V7.3.pdf). |
| D1–D10 | DPYR selections use the same X1SON DPY land pattern, including the two different diode MPNs. The 0.30 × 0.50 mm lands at 0.70 mm centers agree with TI's example. [TI DPY drawing](https://www.ti.com/lit/ds/symlink/tpd1e01b04.pdf). |
| Q1, DMG2305UX-7 | Selected package is SOT-23, matching the placed standard SOT-23 footprint. |
| L10, DFE201210U-2R2M=P2 | Correct custom 2.0 × 1.2 mm inductor pattern; lands 0.55 × 1.20 mm at ±0.725 mm. Both pad rectangles follow its −90° placement correctly; the existing orientation regression passes. [Murata series drawing](https://www.murata.com/~/media/webrenewal/products/inductor/chip/tokoproducts/wirewoundmetalalloychiptype/m_dfe201210u.ashx?la=en). |
| X1, CM8V-T1A | Correct two-terminal custom footprint, 0.80 × 1.50 mm lands and 0.70 mm inner gap. [Micro Crystal recommended land pattern, §4.2](https://www.microcrystal.com/fileadmin/Media/Products/32kHz/App.Manual/CM8V-T1A_Product-Doc.pdf). |
| BT1, CR2032-BS-6 | Correct selected-holder drawing dimensions: 1.9 × 5 mm lands at ±15.3 mm. The detailed 3D model is a documented Q&J visualization substitute, not exact Lian Xin CAD. [Drawing provenance](../../lib/footprint-sources/CR2032-BS-6.md). |
| J4 / test points / fiducials | Correct TC2050-NL 10-contact pattern with three guide holes; 1 mm test pads have no paste, including back-side TP10. Both fiducials use the same 0.5 mm copper/1 mm mask pattern without paste. |

## Verification and limits

KiCad CLI DRC with zone refill, schematic parity, and all severities: **2 errors, 47 warnings, 0 unconnected items, 0 parity issues**. No exclusion was added. Warnings include ten library-footprint differences, 35 silkscreen/text warnings, one dangling track, and one dangling via. Pad geometry comparison isolates the five capacitor errors above; library warnings do not all indicate incorrect copper lands. Existing ignored checks, including missing courtyard and footprint filters/types, are listed in the DRC JSON.

Rendered front copper, mask, paste, fabrication and courtyard layers to [SVGs](layers/), inspected [front copper](front-copper-components.png), and inspected the [top 3D view](top.png) and [power-area detail](power-3d.png). No obvious neighboring component-body collision was seen. This is visual review of the available models, not an exact manufacturer-CAD interference certification or enclosure assembly test.

Existing focused tests: `python3 -m unittest tests.test_inductor_footprint tests.test_bl54l15 -q` — **4 passed**. No test or approval of already exported Gerbers/BOM/CPL is implied; regenerate production files after corrections. Supply ripple, capacitor bias and physical prototype qualification remain separate from this footprint review.
