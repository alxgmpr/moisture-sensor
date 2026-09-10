"""Render an inclusive frame range; configure Metal in every Blender process.
Usage: Blender -b clean.blend --python render_clean.py -- 1 452
"""
import bpy
import sys
from pathlib import Path

s = bpy.context.scene
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == 'METAL'
assert any(d.use for d in prefs.devices), 'No Metal render device available'
s.cycles.device = 'GPU'
print('RENDER_DEVICES', [(d.name, d.type, d.use) for d in prefs.devices], flush=True)
args = sys.argv[sys.argv.index('--') + 1:]
start, end = map(int, args)
assert 1 <= start <= end <= 452
s.frame_start, s.frame_end = start, end
s.render.filepath = str(Path(bpy.data.filepath).parent / 'frames') + '/'
s.render.use_overwrite = True
bpy.ops.render.render(animation=True)
