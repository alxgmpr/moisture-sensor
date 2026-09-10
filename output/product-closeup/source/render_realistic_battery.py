"""Render an inclusive frame range; configure OptiX in every Blender process.
Usage: Blender -b battery.blend --python render_clean.py -- 1 452
"""
import bpy
import sys
from pathlib import Path

s = bpy.context.scene
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == 'OPTIX'
assert any(d.use for d in prefs.devices), 'No OptiX render device available'
s.cycles.device = 'GPU'
# Keep the accurate guided OIDN filter, but execute it on the render GPU.
s.cycles.denoising_use_gpu = True
s.render.threads_mode = 'FIXED'
s.render.threads = 16
print('RENDER_DEVICES', [(d.name, d.type, d.use) for d in prefs.devices], flush=True)
args = sys.argv[sys.argv.index('--') + 1:]
start, end = map(int, args)
assert 1 <= start <= end <= 452
s.frame_start, s.frame_end = start, end
s.render.filepath = str(Path(bpy.data.filepath).parent / 'frames') + '/'
s.render.use_overwrite = True
bpy.ops.render.render(animation=True)
