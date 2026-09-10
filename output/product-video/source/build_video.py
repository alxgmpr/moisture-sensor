import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix
OUT=Path(__file__).resolve().parents[1]
s=bpy.data.scenes['01 • Bare PCB'];bpy.context.window.scene=s;s.name='Product film • coin cell installed'
for old in list(bpy.data.scenes):
 if old!=s:bpy.data.scenes.remove(old)
# Center the actual board on a single animated turntable. Keep the holder, cell and DNP module.
rig=bpy.data.objects.new('Turntable • full assembled PCB',None);s.collection.objects.link(rig)
for o in list(s.objects):
 if o.type in {'MESH','FONT'} and 'Seamless' not in o.name:
  world=o.matrix_world.copy();o.parent=rig;o.matrix_world=world;o.location.y+=.040;o.location.z+=.006
rig.rotation_mode='XYZ'
for f,angle in [(1,math.radians(-30)),(193,math.radians(330))]:
 rig.rotation_euler=(math.radians(4),math.radians(-3),angle);rig.keyframe_insert(data_path='rotation_euler',frame=f)
if rig.animation_data:
 action=rig.animation_data.action
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for k in curve.keyframe_points:k.interpolation='LINEAR'
s.frame_start=1;s.frame_end=192;s.render.fps=24
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.055
s.cycles.max_bounces=6;s.render.use_persistent_data=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=(d.type=='METAL')
s.cycles.device='GPU'
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
s.view_settings.exposure=-2.1
# Clean warm-white studio with broad highlights and a restrained contact shadow.
floor=next(o for o in s.objects if 'Seamless' in o.name)
m=floor.data.materials[0].copy();floor.data.materials[0]=m;m.name='Studio • warm porcelain'
p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.64,.63,.61,1);p.inputs['Roughness'].default_value=.52
for l in list(m.node_tree.links):
 if l.to_socket==p.inputs['Normal']:m.node_tree.links.remove(l)
for o in s.objects:
 if o.type=='LIGHT':
  o.data=o.data.copy()
  o.location.y+=.04
  o.rotation_euler=(Vector((0,0,.01))-o.location).to_track_quat('-Z','Y').to_euler()
  o.data.color=(1,.98,.95) if 'warm' in o.name.lower() else (.90,.95,1)
s.world=s.world.copy();s.world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.74,.8,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.35
cam=s.camera;cam.data=cam.data.copy();cam.location=(.16,-.235,.285);target=Vector((0,0,.010));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.285;cam.data.dof.use_dof=False;cam.data.clip_start=.001
s['Notes']='8-second seamless 360-degree studio rotation. Actual PCB plus existing holder and nominal CR2032; DNP U1 included. No enclosure. 24 fps, 1280x720. All procedural materials embedded.'
s.frame_set(1);s.use_fake_user=True
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'moisture-sensor-turntable.blend'))
# Inspect a full-size still before rendering all frames.
s.render.filepath=str(OUT/'poster.png');bpy.ops.render.render(write_still=True)
