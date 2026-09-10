#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
SCENE=output/product-closeup/clean/moisture-sensor-clean-2k60.blend
PYTHON=output/product-closeup/clean/qa/.venv/bin/python
"$PYTHON" output/product-closeup/source/measure_temporal.py output/product-closeup/clean/qa/baseline output/product-closeup/clean/frames > output/product-closeup/clean/qa/temporal-comparison.json
"$BLENDER" -b "$SCENE" --python-exit-code 1 --python output/product-closeup/source/render_clean.py -- 1 214
"$BLENDER" -b "$SCENE" --python-exit-code 1 --python output/product-closeup/source/render_clean.py -- 245 452
bash output/product-closeup/source/encode_clean.sh
