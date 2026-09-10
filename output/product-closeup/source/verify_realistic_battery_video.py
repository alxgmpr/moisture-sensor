"""Validate frame sequence and encoded video after the clean render completes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import numpy as np
from PIL import Image

out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'battery-realistic'
video = out / 'moisture-sensor-realistic-battery-2k60.mp4'
assert video.is_file(), 'Clean video has not been encoded'
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_streams', '-show_frames', '-show_entries', 'stream=codec_name,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_frames:frame=best_effort_timestamp_time', '-of', 'json', str(video)]))
stream = probe['streams'][0]
assert stream['codec_name'] == 'hevc' and stream['pix_fmt'] == 'yuv420p10le', 'Final master must preserve shading with 10-bit HEVC'
assert (stream['width'], stream['height']) == (2560, 1440)
assert stream['avg_frame_rate'] == stream['r_frame_rate'] == '60/1'
assert int(stream['nb_frames']) == 480
pts = np.array([float(f['best_effort_timestamp_time']) for f in probe['frames']])
assert len(pts) == 480 and np.allclose(np.diff(pts), 1/60, atol=1e-6), 'Dropped or unevenly timed frames'
hashes = []
for f in range(1, 481):
    path = out / 'frames' / f'{f:04d}.png'
    with Image.open(path) as im:
        im.load()
        assert im.size == (2560, 1440)
        hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
assert len(set(hashes[:452])) == 452, 'Duplicated moving frames'
assert all(h == hashes[451] for h in hashes[452:]), 'Final static hold changes'
subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'], check=True)
report = {'passed': True, 'resolution': [2560,1440], 'fps':60, 'frames':480, 'duration_s':8, 'unique_rendered_frames':452, 'duplicated_frames_only_in_final_hold':True, 'constant_frame_timing':True, 'all_pngs_decoded':True, 'mp4_decode_errors':0}
(out / 'video-audit.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
