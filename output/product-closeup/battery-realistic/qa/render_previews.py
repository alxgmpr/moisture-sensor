import bpy
from mathutils import Vector
from pathlib import Path
s=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
assert any(d.use for d in prefs.devices)
s.cycles.device='GPU'
out=Path('/srv/blender/jobs/battery-preview')
s.frame_set(1);s.render.filepath=str(out/'opening.png');bpy.ops.render.render(write_still=True)
cam=s.camera;cam.animation_data_clear();cam.data.lens=75
can=bpy.data.objects['CR2032 | installed positive can'];rig=can.parent
focus=rig.matrix_world@(can.location+Vector((0,0,.0016)))
s.render.resolution_x=1600;s.render.resolution_y=1200
for label,offset in [('hero',(0,-.06,.070)),('side',(0,-.09,.018))]:
    cam.location=focus+(rig.matrix_world.to_3x3()@Vector(offset))
    cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
print('PREVIEW_RENDERS_COMPLETE',flush=True)
