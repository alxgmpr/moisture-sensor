#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
python3 - <<'PY'
from pathlib import Path
folder=Path('output/product-video/frames-hd')
assert all((folder/f'{i:04d}.png').is_file() for i in range(1,193)), 'Missing render frames'
PY
ffmpeg -hide_banner -loglevel warning -y -framerate 24 -start_number 1 -i output/product-video/frames-hd/%04d.png -frames:v 192 -vf 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p' -c:v libx264 -preset slow -crf 16 -movflags +faststart -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an output/product-video/moisture-sensor-turntable.mp4
ffprobe -v error -show_entries stream=codec_name,width,height,avg_frame_rate,nb_frames:format=duration,size -of json output/product-video/moisture-sensor-turntable.mp4 > output/product-video/video-audit.json
ffmpeg -v error -i output/product-video/moisture-sensor-turntable.mp4 -f null -
