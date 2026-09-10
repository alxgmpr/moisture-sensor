#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
KICAD=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
OUT=output/product-3d
"$KICAD" pcb drc --output "$OUT/drc.rpt" --severity-error --exit-code-violations nrf-moisture-sensor.kicad_pcb
"$KICAD" sch erc --output "$OUT/erc.rpt" --severity-error --exit-code-violations nrf-moisture-sensor.kicad_sch
# DNP and unspecified components remain included: deliberately omit --no-dnp and --no-unspecified.
"$KICAD" pcb export glb --force --subst-models --include-tracks --include-pads --include-zones --include-silkscreen --include-soldermask --cut-vias-in-body --user-origin 77x77mm -o "$OUT/pcb-full.glb" nrf-moisture-sensor.kicad_pcb
"$KICAD" pcb export step --force --subst-models --include-pads --cut-vias-in-body --user-origin 77x77mm -o "$OUT/pcb-full.step" nrf-moisture-sensor.kicad_pcb
.venv-cq/bin/python "$OUT/source/prepare_case.py"
.venv-cq/bin/python "$OUT/source/check_case_fit.py"
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python "$OUT/source/build_studio.py"
