"""Build a separate final-quality scene from the existing 1440p60 animation."""
from pathlib import Path
import bpy
import runpy

out = Path(__file__).resolve().parents[1] / 'clean'
out.mkdir(exist_ok=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = 256
s.cycles.use_adaptive_sampling = True
s.cycles.adaptive_threshold = .01
s.cycles.adaptive_min_samples = 64
s.cycles.use_denoising = True
s.cycles.denoiser = 'OPENIMAGEDENOISE'
s.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
s.cycles.denoising_prefilter = 'ACCURATE'
s.cycles.seed = 0
s.cycles.use_animated_seed = False
s.render.use_persistent_data = True
s.render.use_motion_blur = True
s.render.motion_blur_shutter = .5
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == 'METAL'
assert any(d.use for d in prefs.devices), 'No Metal GPU found'
s.cycles.device = 'GPU'
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGB'
s.render.image_settings.color_depth = '8'
s.render.image_settings.compression = 35
s.render.filepath = str(out / 'frames') + '/'
s.frame_start = 1
s.frame_end = 480
s.frame_set(1)
s['Notes'] = '1440p60 native animation. Cycles 256 samples, 0.01 adaptive threshold, minimum 64 samples, accurate albedo/normal denoising, 180-degree motion blur. Original camera, geometry and light animation retained. Final hold begins at frame 452.'
runpy.run_path(str(Path(__file__).with_name('verify_clean_scene.py')))
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'moisture-sensor-clean-2k60.blend'))
