# Board completion checklist

Work through in order; update results after each verified batch. Design edits use
KiCad's live GUI. Shell/CLI use is for read-only analysis, backups, checks and
documentation. Never run the retired board/schematic generators. Save in KiCad
before running checks; synchronize schematic changes through Update PCB from
Schematic. Preserve the existing dirty working tree.

## 1. Parts and reference baseline — in progress

- [ ] Confirm nRF54L15-QFAA-R7 production reference/silicon compatibility.
- [ ] Confirm exact footprint sizes for Nordic support components.
- [x] Record current backups and initial ERC/DRC/parity.

## 2. Local nRF placement

- [x] Restore standard 0201 C1/C2/C4/C5/C7/C8/C10/C12/C13 and FB1/R1 footprints;
      standard 0402 C3 and 0603 L1. Update schematic assignments first.
- [ ] Move C1 next to DECD, C2/C12/FB1 next to DECA, C5 next to DECRF,
      and C10 next to VDD47/48; provide short ground returns.
- [x] Move I2C pull-ups out of the local power/oscillator placement area as needed.
- [ ] Re-place X2 for short single-layer XC1/XC2 routing with grounded case pads.
- [x] Check courtyards, clearances, netlist identity and schematic/PCB parity.
      These checks pass at handoff; placement still needs routing validation.

## 3. Route critical local connections

- [x] Configure GUI interactive router for shove/walk-around and H/V/45 routing.
- [ ] Route nRF internal power/filter nets first; minimize loops and vias.
- [ ] Route XC1/XC2 on F.Cu without signal vias; preserve crystal pin numbering.
- [ ] Refill planes and pass DRC/connectivity after the local batch.

## 4. RF review

- [ ] Compare matching geometry and inner-plane cutouts against the selected reference.
- [ ] Preserve C6 → VSS_PA and C9 bottom-only grounding.
- [ ] Verify C11 local ground and controlled-impedance R27/AE1 feed and all-layer antenna keepout.
- [ ] Confirm fab stack/impedance geometry and enclosure antenna/coax clearance.

## 5. Remaining routing

- [ ] Improve PMIC VINT/PVSS capacitor loop if placement permits.
- [ ] Clean up digital routes with the interactive router: avoid unnecessary vias,
      acute corners, short jogs and detours; keep the In1 reference intact.
- [ ] Preserve driven shielding and separation around sensing routes.
- [ ] Verify SHT45 and FDC bypass routing and thermal/copper keepouts.

## 6. Manufacturing checks

- [ ] Reconcile library symbol and footprint differences deliberately.
- [ ] Remove dangling schematic wire and repair silkscreen warnings.
- [ ] Verify all 3D models, courtyards, battery removal and programming access.
- [ ] Final ERC, DRC, zero unrouted, zero parity, netlist fingerprint and repo checks.

## 7. BOM and release package

- [ ] Lock critical capacitor/inductor MPNs and effective capacitance at bias/temperature.
- [ ] Finish insertion mark/stop, probe edge sealing, coating mask and assembly notes.
- [ ] Validate mechanical enclosure/antenna fit.
- [ ] Generate and visually review Gerbers, drills, position files, BOM and assembly drawings.
- [ ] Record final source hashes and release status; do not order automatically.

## 8. Physical prototype validation

- [ ] Verify boot/PMIC sequencing and low-battery radio bursts with aged-cell impedance.
- [ ] Measure sleep/active current and estimate life from measured duty cycle.
- [ ] Check oscillator startup/trim and RF performance in the final enclosure.
- [ ] Calibrate the coated probe in representative soil; check range and shield loading.
- [ ] Verify humidity response, moisture ingress and long-term stability.

## Session log

- 2026-09-04: Starting from the completed audit bypass corrections. Baseline copied
  to `tmp/board-finish/baseline/`. Previous check: 0 DRC errors, 18 warnings,
  0 unrouted, 0 parity, 0 ERC errors, 23 ERC warnings, 35 repository checks passed.
- 2026-09-04 handoff: GUI routing stopped after unreliable canvas interaction made
  precise routing impractical. Saved and refilled in KiCad. Current DRC: 7
  track-width errors, 3 missing connections, 47 warnings; no courtyard overlaps,
  shorts or clearance errors reported. Netlist identity (62 nets), schematic/PCB
  parity and all 35 repository checks pass. This is an incomplete routing state,
  not a fabrication release. Finish the exact routes and cleanup in
  [the routing handoff](docs/board-routing-handoff-2026-09-04.md) before continuing
  with RF review and the remaining checklist. Placement changes are provisional
  until those routes pass DRC.

- [ ] Tune AE1/R27/C29 in the assembled enclosure; approve radiated performance
  and changed radiator-to-battery spacing. See LAYOUT.md §3.
