"""Run inside Blender against the rebuilt scene before rendering."""
import bpy
s = bpy.context.scene
assert (s.render.resolution_x, s.render.resolution_y, s.render.fps, s.frame_start, s.frame_end) == (2560, 1440, 60, 1, 480)
assert s.render.engine == 'CYCLES', 'Final quality requires path-traced shadows'
assert s.cycles.seed == 0 and not s.cycles.use_animated_seed, 'Sampling must not randomize between frames'
assert s.cycles.samples >= 256 and s.cycles.adaptive_threshold <= .01
assert s.cycles.adaptive_min_samples >= 64
assert s.cycles.use_denoising and s.cycles.denoising_input_passes == 'RGB_ALBEDO_NORMAL'
assert s.render.use_motion_blur and .25 <= s.render.motion_blur_shutter <= .5
rig = bpy.data.objects['Turntable • full assembled PCB']
positions = []
angles = []
for f in range(1, 481):
    s.frame_set(f)
    positions.append(s.camera.location.copy())
    angles.append(rig.rotation_euler.z)
assert all(0 <= b-a < .025 for a,b in zip(angles, angles[1:])), 'Rotation jumps or reverses'
assert all((b-a).length < .003 for a,b in zip(positions, positions[1:])), 'Camera jumps'
assert all((p-positions[451]).length < 1e-8 for p in positions[452:])
s.frame_set(1)
print('PASS: clean render profile, native 60fps, continuous motion, static ending')
