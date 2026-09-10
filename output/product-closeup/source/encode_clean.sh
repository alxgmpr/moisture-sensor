#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
output/product-closeup/clean/qa/.venv/bin/python - <<'PY'
from pathlib import Path
import shutil
from PIL import Image
folder = Path('output/product-closeup/clean/frames')
for frame in range(1, 453):
    with Image.open(folder / f'{frame:04d}.png') as im:
        im.verify()
for frame in range(453, 481):
    shutil.copyfile(folder / '0452.png', folder / f'{frame:04d}.png')
PY
ffmpeg -hide_banner -loglevel warning -y -framerate 60 -start_number 1 -i output/product-closeup/clean/frames/%04d.png -frames:v 480 -vf 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p10le' -c:v libx265 -preset slow -crf 16 -tag:v hvc1 -x265-params log-level=error -movflags +faststart -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an output/product-closeup/clean/moisture-sensor-clean-2k60.mp4
output/product-closeup/clean/qa/.venv/bin/python output/product-closeup/source/verify_clean_video.py
