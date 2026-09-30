> 2026-09-09 cost revision: U4 is now Sensirion SHT40-AD1F-R2. The existing SHT4x footprint, membrane handling, geometry, and legacy SHT45-named model/rule areas are retained. See [cost revision](docs/cost-reduction-2026-09-09/README.md).

# nRF Moisture Sensor — completion checklist

Current fabrication handoff: [2026-09-09 verified files and order notes](production/fab-2026-09-09/README.md).
Routing has zero unconnected items, zero unaccepted DRC errors and zero parity issues.
The user accepted the two +3V3 vias in the GND-via exclusion corridor. Fresh
Gerbers, drills, BOM/CPL, separate manual-module stencil and assembly drawings
are in that handoff directory. No order has been placed.
C26–C28 order codes are populated; C21/C23 effective-capacitance qualification remains open.
The older routing handoff below is retained as history; the current review takes precedence.

# Board completion checklist — BL54L15 routing handoff

Current source is the actual KiCad schematic/PCB. Use CLI or GUI as appropriate,
as authorized by Alex. Do not run the retired full-board/schematic generators.
Preserve unrelated edits. The previous checklist is preserved in
[history](docs/bl54l15/history/BOARD-FINISH-before.md).

- [x] Replace bare U1 with Ezurio 453-00001R, verified 39-pad symbol/land pattern.
- [x] Remove obsolete RF, DCDC and 32 MHz host parts/nets; retain external X1.
- [x] Preserve GPIO assignments, nPM2100, CR2032, FDC1004, SHT45 and J4.
- [x] Place module on board edge; implement all-layer antenna keepouts and grounds.
- [x] Separate complete-product BOM from JLC DNP/position/paste outputs.
- [x] Run ERC, physical DRC, parity, repository checks and visual review; see
      [the current results](docs/bl54l15/verification.md).
- [x] Finish remaining digital/power routing and remove abandoned anchors.
      Preserve X1/C3 local routes and antenna keepouts. Refill; require zero
      unconnected items and no new physical DRC errors.
- [ ] Reconcile existing library mismatch warnings and R22/R23 silk overlap.
- [ ] Qualify C21/C23 effective capacitance and module VOUT loading. C26–C28 and BT1 now have source selections.
- [ ] Implement production firmware clock configuration and HP-mode radio windows.
- [ ] Qualify ≤10 mV module VDD ripple/noise, total effective VOUT capacitance,
      cold start, low-battery bursts, clock startup/trim and timed System OFF wake.
- [ ] Validate module hot-air assembly profile without overheating SHT45/PTFE.
- [ ] Resolve or qualify the enclosure metal-spacing shortfall through radiated
      testing with installed battery and lid; DRC does not establish RF compliance.
- [ ] Complete probe insertion mark, capillary barrier, coating mask and sealing;
      preserve the IP54 target, sensor opening and battery removal access.
- [x] Re-export and visually approve final Gerbers/drills/BOM/positions/stencils,
      source hashes and assembly drawings after routing. Do not order automatically.
- [ ] Measure current/life, coated-probe calibration, humidity response and ingress.

## Protection revision

- [x] Q1 reverse-battery PMOS; battery/debug/probe ESD clamps and series isolation.
- [x] Zero new physical DRC errors and zero parity issues; original 15 missing module connections remain.
- [ ] Qualify ESD/leakage, low-cell startup, SWD and sensing with the new parts.
- [x] Move D1 to front PCBA; refine holder courtyard and install TI diode STEP model.
- [ ] Do not claim sustained OVP or a battery fuse; neither is fitted.

See [protection report](docs/protection/README.md) for current details.
