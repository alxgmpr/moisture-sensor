# PCB design improvement log — 2026-09-02

This is the working review and implementation log for the CR2032 + nPM2100
revision. The older `audit-2026-07-31.md` describes the retired
nPM1300/rechargeable/solar layout and is retained only as design history.

## Working rules

- Make small, reviewable batches and run ERC/DRC after each batch.
- Lock exact orderable parts before final placement and routing.
- Use the matching Nordic nRF54L15 reference revision for the selected silicon.
- Do not waive electrical or clearance errors that can be fixed at the source.
- Preserve a solid In1.Cu ground plane; keep switching and sensing loops local.
- Validate RF, capacitance, temperature, and battery behavior in the final
  enclosure with the production coating and mechanical stack.
- Production assembly will use PCBA; 0201 passives are acceptable. Prefer the
  Nordic reference packages wherever they improve RF or decoupling geometry.

## Current baseline

- [x] Synchronize schematic and PCB for the nPM2100/CR2032 architecture.
- [x] Remove obsolete nPM1300, solar, USB, and rechargeable-power footprints from the PCB.
- [x] Remove obsolete routing, vias, and power-section copper left by the update.
- [x] Resolve all schematic/PCB parity errors before detailed placement work.
- [x] Resolve ERC errors in the custom nPM2100 symbol and PG/RESET circuitry.
- [x] Re-run ERC and DRC and record the new baseline below.

Baseline observed before implementation:

- ERC: 23 violations, including 2 electrical errors and 21 library mismatches.
- DRC after zone refill: 38 violations and 43 unconnected items.
- Schematic/PCB parity: 85 issues.

Baseline after schematic/PCB synchronization:

- ERC: 0 errors and 22 warnings. Twenty-one warnings are library-copy
  mismatches; one is an unconnected wire endpoint.
- Schematic/PCB parity: 0 issues.
- DRC: 242 violations and 30 unconnected items. Most new violations are the
  expected result of replacing the 32-pad nPM1300 footprint with the 16-pad
  nPM2100 footprint while obsolete nPM1300 routing and vias remain in place.

## nRF54L15 and RF

- [ ] Lock the exact nRF54L15 silicon/order code and matching reference revision.
- [ ] Restore Nordic reference packages and placement for the support network:
  C1, C2, C4, C5, C7, C8, C10, C12, C13, FB1, and R1 as 0201; C3 as 0402;
  L1 as 0603.
  Decision: 0201 assembly is approved because the board will be PCBA-built.
- [ ] Preserve the exact DECA/DECD component values; do not consolidate them.
- [ ] Reroute X2/XC1/XC2 symmetrically. The incomplete XC2 route that violated
  pad-4 ground clearance has been removed; both oscillator nets are intentionally
  left unrouted until the placement pass.
- [ ] Connect C11's RF shunt ground directly to the ground plane with an
  immediate via and minimize its branch length.
- [ ] Keep the RF chain on F.Cu, without RF vias, over uninterrupted In1.Cu.
- [ ] Set the routed RF nominal width consistently to 0.36 mm in project rules,
  netclasses, and documentation.
- [x] Lock Molex 2069940100 on the inside RF-end short wall, perpendicular to
  the PCB, with ≥25 mm radiator-to-cell spacing and restrained perimeter coax.
- [ ] VNA-test the populated RF path in the final enclosure with the cell and
  representative wet soil present.

## nPM2100 and CR2032

- [x] Lock BT1 as MPD BU2032SM-BT-GTR and L10 as Murata DFE201210U-2R2M=P2.
- [x] Place and locally route the nPM2100 switch loop to match Nordic's topology.
- [x] Place the small HF capacitors closest to VBAT and VINT, with bulk directly
  behind and short same-layer ground returns into the exposed-pad ground area.
- [ ] Verify effective capacitance after DC bias, tolerance, temperature, and
  aging: VBAT >= 3.5 uF, VINT >= 3.5 uF, VOUT 0.7–15 uF.
- [ ] Retain 10 uF VBAT, 22 uF VINT, and 2.2 uF VOUT unless exact-part derating
  or testing requires a change.
- [ ] Add optional, normally unpopulated reservoir-cap footprints on VBAT and
  VINT for end-of-life cell testing; do not add bulk to VOUT casually.
- [x] Retain the accepted polarity-marking/mechanical mitigation; no reverse-
  protection FET is added unless the architecture decision is reopened.
- [x] Preserve battery replacement clearance, contact masking, visible polarity,
  and separation from the antenna and moisture entry paths.

## FDC1004 and soil probe

- [ ] Add a local 100 nF X7R bypass directly across U3 VDD/GND.
- [ ] Move the existing 1 uF bypass directly behind the 100 nF capacitor.
- [ ] Keep U3 near the probe boundary and route CIN1/CIN2 as short, guarded
  traces separated from the nPM2100 switch node and digital traffic.
- [ ] Verify SENSE1, SENSE2, and SHLD connectivity after the PCB sync.
- [ ] Add an insertion mark and preferably a physical stop in the gap between
  the reference and measurement electrodes, about 41 mm below the shoulder.
- [ ] Coat the buried probe faces and routed FR-4 edges using the production
  coating, then calibrate the completed assembly.
- [ ] Verify input offset, measurement swing, shield loading, and wet-soil
  behavior on prototypes.

## SHT45 and water ingress

- [ ] Place a 100 nF 0201 capacitor within about 1 mm of U4 on the isolated tab.
- [ ] Keep copper and planes out from under the sensing body.
- [ ] Increase exposure beyond the enclosure wall to roughly 3–5 mm or provide
  a ventilated, isolated pocket that avoids the enclosure thermal boundary layer.
- [ ] Mask the sensing membrane during selective conformal coating.
- [ ] Use only fully cured, low-outgassing neutral-cure sealing materials near
  the sensor; avoid acetic-cure silicone and VOC exposure.
- [ ] Replace a simple moving RTV joint at the probe slot with a grommet, boot,
  potting well, or other strain-relieved capillary barrier.
- [ ] Document the product-level ingress rating after accounting for the probe
  and humidity-sensor openings.

## BOM and documentation

- [ ] Add manufacturer, exact MPN, tolerance, voltage rating, dielectric, and
  package fields for every electrically critical capacitor and inductor.
- [x] Resolve the battery-holder and L10 footprint/BOM disagreements.
- [ ] Exclude power/global symbols that currently leak into the BOM as `1?`,
  `2?`, and similar pseudo-components.
- [ ] Regenerate enclosure-fit drawings and STEP checks for the CR2032 design.
- [x] Update or clearly retire nPM1300/rechargeable/solar instructions in `LAYOUT.md`,
  `NEXT-STEPS.md`, and other mechanical documentation.

## Implementation batches

### Batch 1 — migration and clean baseline

Status: complete

- [x] Inspect the live KiCad project and identify which PCB items are obsolete.
- [x] Correct the nPM2100 schematic symbol/ERC issues.
- [x] Synchronize the PCB to the schematic without routing the new power block.
- [x] Run ERC/DRC and record the remaining actionable baseline.
- [x] Remove obsolete PMIC routing and vias, preserving unrelated sensor/RF
  copper and the enclosure/mechanical layers.

### Results and decisions

Record each completed batch here with the date, files changed, ERC/DRC result,
and any design decision that affects later work.

#### 2026-09-02 — Batch 1, migration baseline

- Corrected nPM2100 VINT pin 15 from power-output to passive in both the library
  and embedded schematic symbol while retaining pin 14 as the rail output.
- Removed the inappropriate PWR_FLAG from the open-drain PG/RESET net.
- Assigned valid hidden references to the custom VBAT/FDC_VDD power symbols and
  numbered the remaining PWR_FLAG symbols without changing component references.
- Updated the PCB from the schematic using reference-based relinking, footprint
  replacement, and deletion of unlocked footprints without schematic symbols.
- Result: zero ERC errors and zero schematic/PCB parity issues. Obsolete power
  copper cleanup is the next step before new nPM2100 placement/routing.

#### 2026-09-02 — Batch 1 cleanup

- Applied KiCad's track/via cleanup after reviewing 106 proposed actions. The
  removed items were redundant vias on the former nPM1300 exposed-pad field,
  shorting vias, obsolete VSET routing, and disconnected former PMIC stubs.
- Removed the incomplete four-segment XC2 route rather than retaining an
  asymmetric oscillator connection. XC1 and XC2 will be routed together.
- Corrected U2 from the inherited 180-degree nPM1300 orientation to 0 degrees,
  placing L10 on the SW/VBAT side of the nPM2100 rather than the GPIO/reset side.
- DRC after zone refill: 19 violations total, comprising 5 placement-related
  errors and 14 warnings, with 31 unconnected items and zero parity issues.
- All five errors are now confined to the provisional U2/L10/C25 placement.
  Final spacing depends on locking the production inductor footprint and power
  floorplan; there are no remaining crystal or stale-routing DRC errors.

#### 2026-09-03 — Assembly decision

- Production method: PCBA.
- 0201 passives: approved, including restoration of Nordic's reference package
  sizes around the nRF54L15.

#### 2026-09-03 — Batch 2, locked mechanics and PMIC placement

- Locked BT1 to MPD `BU2032SM-BT-GTR` and created the manufacturer-pattern SMT
  footprint: 3.20 × 4.20 mm pads on 29.30 mm centres, 32.50 mm copper span,
  31.86 × 22.40 mm assembly envelope, polarity marks, and a dedicated removal-
  tool courtyard. Placed at board-local (17.0,42.0), positive toward U2.
- Locked L10 to Murata `DFE201210U-2R2M=P2` and created the 2.00 × 1.20 mm
  footprint with 0.55 × 1.20 mm pads, 1.45 mm centres, 0.90 mm inner gap, and
  2.70 × 1.90 mm courtyard.
- Replaced hand-solder lands on C21/C23/C25 with standard PCBA 0402 footprints,
  compacted U2/L10/C21–C25 below BT1, and routed the SW, VINT, VBAT, and VOUT
  local loops without hard DRC violations.
- Moved J4 within the digital/service region to clear the installed-cell and
  removal envelopes; J5, U1, and the Nordic RF support placement did not move.
- Locked the enclosure antenna to Molex `2069940100`: vertical on the inside
  RF-end short wall, ≥25 mm from the cell, nylon RF-end screws, and restrained
  perimeter coax.
- Confirmed the accepted reverse-cell strategy remains visible polarity plus
  handling controls; no reverse-protection FET was added.
- Validation after zone refill: schematic/PCB parity 0; ERC 0 errors and 22
  warnings; PCB geometry/rules 0 errors and 13 warnings; 22 unrouted electrical
  connections remain. Reports are generated under `tmp/kicad-check/` and the
  remaining items are reported in the implementation handoff.
