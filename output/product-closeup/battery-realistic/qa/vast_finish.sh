#!/bin/bash
set -euo pipefail
cd /root/render
while [[ ! -f render.exit ]]; do sleep 5; done
[[ $(cat render.exit) == 0 ]]
python3 - <<'PY'
from pathlib import Path
import shutil
from PIL import Image
folder=Path('frames')
for frame in range(1,453):
    with Image.open(folder/f'{frame:04d}.png') as im: im.verify()
for frame in range(453,481):shutil.copyfile(folder/'0452.png',folder/f'{frame:04d}.png')
PY
ffmpeg -hide_banner -loglevel warning -y -framerate 60 -start_number 1 -i frames/%04d.png -frames:v 480 -vf 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p10le' -c:v libx265 -preset slow -crf 16 -tag:v hvc1 -x265-params 'log-level=error:pools=16' -movflags +faststart -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an moisture-sensor-realistic-battery-2k60.mp4 > encode.log 2>&1
python3 verify_realistic_battery_video.py /root/render > verify-video.log 2>&1
sha256sum moisture-sensor-realistic-battery-2k60.mp4 > video.sha256
printf 'COMPLETE\n' > finish.done
