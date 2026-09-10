import bpy,json
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]
s=bpy.data.scenes['01 • Bare PCB'].copy();s.name='04 • Electronics detail';s.use_fake_user=True;bpy.context.window.scene=s
cam=s.camera.copy();cam.data=s.camera.data.copy();s.collection.objects.link(cam);s.camera=cam
cam.location=(.069,-.075,.115);target=Vector((0,.002,.005));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=60;cam.data.dof.focus_distance=(target-cam.location).length;cam.data.dof.aperture_fstop=20
for scene in bpy.data.scenes:scene.use_fake_user=True
s.render.filepath=str(OUT/'04-electronics-detail.png')
bpy.ops.render.render(write_still=True)
bpy.context.window.scene=bpy.data.scenes['01 • Bare PCB']
audit={s.name:{'mesh_count':sum(o.type=='MESH' for o in s.objects),'dnp_U1_meshes':sum('U1' in o.name for o in s.objects),'camera':s.camera.name,'resolution':[s.render.resolution_x,s.render.resolution_y]} for s in bpy.data.scenes}
assert len(audit)==4
assert all(a['dnp_U1_meshes']>=1 for a in audit.values())
(OUT/'scene-audit.json').write_text(json.dumps(audit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'moisture-sensor-studio.blend'))
