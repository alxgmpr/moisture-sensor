# Review manufacturing exports

Follow the repository's KiCad CLI export approach. The maintained schematic
and PCB are authoritative; the retired full-board generators must not be run.
`tools_export_bl54l15.py` automates the CLI commands and adds the two assembly
stages. It only writes the output directory, never the maintained design.

From the repository root, using KiCad 10.99 (file format 20260828):

```sh
export KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
"$KICAD_CLI" sch erc --format json -o docs/bl54l15/erc.json moisture-sensor.kicad_sch
"$KICAD_CLI" pcb drc --refill-zones --save-board --schematic-parity --format json -o docs/bl54l15/drc.json moisture-sensor.kicad_pcb
python3 -m unittest discover -s tests -v
python3 tools_export_bl54l15.py
```

Default output is `production/bl54l15-routing-review/`, ignored by git as with
other manufacturing outputs. It contains:

| Output | Intended use |
|---|---|
| `fabrication-review/` | Four copper, two mask, two silk and Edge.Cuts Gerbers; separate PTH/NPTH Excellon drills and drill map |
| `product-bom.csv` | All 20 fitted product components, including U1 with DigiKey cut-tape order code |
| `jlc-bom.csv` | 19 candidate outsourced placements; excludes U1, includes procurement status |
| `jlc-upload-bom-REVIEW.csv` | JLC column format; unresolved parts remain blank/candidate |
| `jlc-positions-REVIEW.csv` | 19 placements, mm, KiCad origin/rotation; no U1 or bare PCB contacts |
| `jlc-paste/` | Derived board and F/B paste Gerbers with U1 omitted |
| `module-hand-fit-paste/` | Derived board and F/B paste Gerbers containing only U1's 39 LGA apertures |
| `schematic-review.pdf`, `layer-review/` | Schematic and layer drawings for inspection |
| `source-sha256.json`, `export-log.json` | Source identity and actual CLI invocations |

The source board keeps the U1 paste/mask/copper lands. A derived copy removes
U1 for JLC paste; another keeps only U1 for manual paste. Main fabrication files
contain no paste layers, avoiding accidental double application. Both paste
stages use the unchanged PCB coordinate origin. The module patch is a land
pattern, not a vendor-designed stencil frame; align from the placement drawing
and use the qualified local process. No iron-access assumption is made.

**These are review files, not a released order package:** 15 missing connections
remain deliberately. C23 bias qualification, C26/C27/C28 exact sourcing and BT1
assembly source remain open. Module supply ripple, clock trim, enclosure RF
clearance and hot-air attachment require physical validation. After routing,
refill, rerun ERC/DRC/parity, require zero unrouted, reconcile warnings, and
visually inspect final Gerbers and assembly rotations before issuing a release.
Do not upload or order this review package.

## Protection revision supersedes the counts above

The 2026-09-04 protection change adds 17 fitted parts, all on F.Cu. D1 sits
beside the positive battery contact in the revised holder courtyard; bottom
assembly/paste is not required for these additions. The exporter supports both
sides. Re-export into a fresh directory after final routing; old production
archives predate this revision. Stock/assembly availability remains open.
See [protection report](../protection/README.md).
