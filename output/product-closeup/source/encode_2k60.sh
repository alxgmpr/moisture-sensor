#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
python3 - <<'PY'
from pathlib import Path
folder=Path('output/product-closeup/frames-2k60-final')
assert all((folder/f'{i:04d}.png').is_file() for i in range(1,481)), 'Missing render frames'
PY
ffmpeg -hide_banner -loglevel warning -y -framerate 60 -start_number 1 -i output/product-closeup/frames-2k60-final/%04d.png -frames:v 480 -vf 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,hqdn3d=0.6:0.4:1.2:0.8' -c:v libx264 -preset slow -crf 15 -profile:v high -level:v 5.1 -movflags +faststart -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an output/product-closeup/moisture-sensor-closeup-2k60.mp4
ffprobe -v error -show_entries stream=codec_name,width,height,avg_frame_rate,nb_frames:format=duration,size -of json output/product-closeup/moisture-sensor-closeup-2k60.mp4 > output/product-closeup/video-audit.json
ffmpeg -v error -i output/product-closeup/moisture-sensor-closeup-2k60.mp4 -f null -
