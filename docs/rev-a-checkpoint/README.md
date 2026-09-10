# Rev A checkpoint before Rev B

This sweep preserves the consolidated development BOM, schematic edits, Alex's
PCB update/routing, synchronized PCB purchasing fields, and the matching JLC
quote export. No revision-B electrical changes are introduced by this checkpoint.

## Manufacturing baseline

- All four maintained KiCad source hashes match the exported
  [source manifest](source-sha256.json).
- [JLC BOM](JLC-BOM.csv): 36 fitted placements, 14 unique purchase rows.
  [Placement file](JLC-CPL.csv), [full product BOM](Product-BOM.csv).
- The BL54L15 module is excluded from JLC assembly and requires manual fitting.
- Full regenerated fabrication package remains in
  `production/jlc-consolidated-quote`, including `JLC-Gerbers.zip`, the module
  stencil and schematic PDF. Regenerable production files remain ignored in Git.
- [ERC](erc.json): zero errors, nine library-symbol mismatch warnings.
- [DRC](drc.json): zero unconnected items and zero schematic parity issues;
  39 warnings and the two previously accepted +3V3-via keepout errors.
  The exact exceptions are preserved in [accepted errors](accepted-drc-errors.json).
- User supplied JLC review screenshot for order SMT026091060334 showing 15
  revised designators. All visible part numbers matched the export. The screenshot
  did not establish placement/orientation approval or confirm order submission.

High-quality front/back raytraced images remain locally in `output/board-raytraced`.
Generated media and scratch files are not part of this source checkpoint.

## Test state and Rev B follow-ups

`python3 -m unittest discover -s tests`: 51 tests run; nine failed assertions
across six test methods (the reservoir test has four failing subtests).
Failures are preserved, not suppressed or converted to passing checks:

| Test | Observed issue / follow-up |
| --- | --- |
| `test_only_bare_copper_footprints_are_model_less` | Expected references still include removed fiducials and omit testpoints/tooling holes. Reconcile the model-coverage list. |
| `test_explicit_economic_selections_match_board` | C26 expectation still names C528974; the implemented common part is C12530. Reconcile the full selected BOM. |
| `test_probe_clamps_have_nearby_ground_vias_in_ground_plane` | D8 has no qualifying GND-plane via within the test's 0.7 mm radius. Investigate the actual return path before altering the test or layout. |
| `test_routing_classes_use_production_safe_dimensions` | SENSE clearance is 0.6 mm in project settings versus 0.2 mm expected. Reconcile intended rules. |
| `test_probe_and_debug_series_resistors_separate_external_nets` | R35 now ends on NRESET; the test still expects SWD_RST from the removed R1 topology. |
| `test_exact_nordic_reference_reservoirs` | C21/C23 now use CL10A106MA8NRNC in both files; the old test requires Nordic-listed 0402 parts. This is an intentional dev selection, not proof of effective-capacitance qualification. |

Before a future release, complete capacitor operating-corner, startup/ripple,
sensing repeatability and reset checks recorded in the
[consolidation decision](../dev-bom-consolidation-2026-09-09.md). Review the
unfiltered SHT40 environmental exposure and development ESD tradeoffs for Rev B.

`git diff --check` passed before the sweep. No tests or design rules were weakened.
