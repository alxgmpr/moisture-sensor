import bpy,math,time
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1];s=bpy.context.scene
rig=bpy.data.objects['Turntable • full assembled PCB'];rig.animation_data_clear();rig.rotation_euler=(math.radians(4),math.radians(-3),math.radians(-30));bpy.context.view_layer.update()
cam=s.camera;cam.animation_data_clear();cam.data.animation_data_clear();cam.data.type='PERSP';cam.data.lens=60;cam.data.dof.use_dof=False
s.frame_start=1;s.frame_end=480;s.render.fps=60;s.render.fps_base=1
s.render.resolution_x=2560;s.render.resolution_y=1440;s.render.resolution_percentage=100
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=32;s.eevee.use_raytracing=True
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=0
s.view_settings.exposure=-2.35
# 4.5 seconds close, three-second eased dolly, half-second final hold.
def ease(t):return t*t*(3-2*t)
for f in range(1,481):
 time_s=(f-1)/60;pull=ease(max(0,min(1,(time_s-4.5)/3)))
 orbit=ease(min(1,time_s/7.5));az=math.radians(-48-18*orbit)
 rig.rotation_euler=(math.radians(4),math.radians(-3),math.radians(-30+360*orbit));rig.keyframe_insert(data_path='rotation_euler',frame=f);bpy.context.view_layer.update()
 direction=Vector((math.cos(az)*.62,math.sin(az)*.62,.785)).normalized()
 focus=rig.matrix_world@Vector((0,.034*(1-pull),.009));distance=.228+(.46-.228)*pull
 cam.location=focus+direction*distance;cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f)
s.frame_set(1);s.use_fake_user=True;s.render.filepath=str(OUT/'frames-2k60-final'/'')
s['Notes']='2560x1440, native 60 fps, 8 seconds. Full product rotation with a tracking close-up for 4.5 seconds; smooth three-second camera dolly back; final half-second hold. EEVEE with ray-traced reflections, 32 samples. Holder, CR2032 cell and DNP U1 retained. Original board geometry unchanged.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'moisture-sensor-closeup-2k60.blend'))
for f,name in [(1,'opening-2k'),(480,'ending-2k')]:
 s.frame_set(f);s.render.filepath=str(OUT/(name+'.png'));start=time.time();bpy.ops.render.render(write_still=True);print('PREVIEW_SECONDS',time.time()-start,flush=True)
