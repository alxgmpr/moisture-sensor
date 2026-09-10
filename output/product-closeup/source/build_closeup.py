import bpy,math,json
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
s=bpy.context.scene;s.name='Close-up • final camera pullback'
rig=bpy.data.objects['Turntable • full assembled PCB'];rig.animation_data_clear();rig.rotation_euler=(math.radians(4),math.radians(-3),math.radians(-30))
bpy.context.view_layer.update()
cam=s.camera;cam.animation_data_clear();cam.data.animation_data_clear();cam.data.type='PERSP';cam.data.lens=60;cam.data.dof.use_dof=False
s.frame_start=1;s.frame_end=192;s.render.fps=24
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.cycles.samples=20;s.cycles.adaptive_threshold=.045;s.render.use_persistent_data=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=(d.type=='METAL')
s.cycles.device='GPU'
def smooth(t):return t*t*(3-2*t)
for f in range(1,193):
 t=(f-1)/191;pull=smooth(max(0,min(1,(f-109)/(180-109))))
 orbit=smooth(min(1,t/.94));az=math.radians(-48-18*orbit)
 direction=Vector((math.cos(az)*.62,math.sin(az)*.62,.785)).normalized()
 focus=rig.matrix_world@Vector((0,.034*(1-pull),.009))
 distance=.228+(.46-.228)*pull
 cam.location=focus+direction*distance;cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f)
s['Notes']='8 seconds, 24 fps. First 4.5 seconds: populated-board close-up with gentle camera orbit. Then a smooth dolly back to reveal the full PCB by 7.5 seconds, followed by a final hold. Coin cell, holder and DNP U1 retained.'
s.frame_set(1);s.render.filepath=str(OUT/'frames'/'')
s.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'moisture-sensor-closeup.blend'))
for f,name in [(1,'opening'),(109,'before-pullback'),(192,'ending')]:
 s.frame_set(f);s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
