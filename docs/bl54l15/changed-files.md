# Files changed for the BL54L15 migration

The repository already contained substantial unrelated uncommitted work.
This list identifies this migration's files; it is not a claim that every line
of the overall git diff was produced here. Earlier design/audit edits remain.

| Files | Migration change |
|---|---|
| `moisture-sensor.kicad_sch` | U1 module, verified pads, retained X1/C3/reset, deleted bare-SoC/RF support, JLC DNP/source fields and annotations |
| `moisture-sensor.kicad_pcb` | Module placement, LGA lands, local support/ground routes, all-layer keepouts, obsolete RF removal, hand-routing anchors |
| `moisture-sensor.kicad_pro`, `.kicad_dru` | Retire obsolete RF net class and bare-SoC RF/escape rules; retain power/sensing constraints |
| `netlist-fingerprint.json`, `sym-lib-table` | Current connectivity and local Ezurio symbol registration |
| `lib/ezurio.kicad_sym` | New verified 39-pin symbol |
| `lib/footprints.pretty/Ezurio_BL54L15_453-00001.kicad_mod` | New manufacturer-derived land pattern, courtyard and pin-1 marker |
| `lib/BL54L15_453-00001_envelope.step`, `tools_3d_models.py` | Nominal module envelope model and current model mapping |
| `BOM.md`, `HARDWARE.md`, `LAYOUT.md` | Current BOM, module support, pin/clock/power/RF/assembly constraints |
| `NEXT-STEPS.md`, `TODO.md` | Current handoff/checklist; old engineering journal preserved and labeled historical |
| `firmware/README.md`, `firmware/BL54L15-port.md` | DK scope preserved; sensor GPIO, clock trim and HP-radio requirements |
| `doc/datasheets/README.md` | Current Ezurio and Nordic configuration source pointers |
| `docs/bl54l15/` | Integration record, source/procurement metadata, before/after reports, preservation report, visuals, assembly/export instructions and pre-migration BOM/checklist |
| `tools_export_bl54l15.py` | Reproducible review exports, separate JLC/module paste and BOM/CPL stages |
| `tests/test_bl54l15.py`, `tests/test_bl54l15_exports.py` | Module pads, land geometry, keepouts and assembly export checks |
| `tests/test_rf_design.py`, `test_pcb_routing_rules.py`, `test_jlc_bom.py`, `test_pcb_assembly_flags.py`, `test_3d_models.py` (all under `tests/`) | Replace obsolete bare-SoC/RF expectations; preserve relevant power/sensor/model/export invariants |

Generated manufacturing files are in `production/bl54l15-routing-review/`
(ignored by git, reproducible). Scratch scripts, downloaded figures and the
starting design snapshot are in `tmp/bl54l15/`; do not rerun its one-shot
migration scripts on the final design. Use the maintained design and export
helper for subsequent work.
