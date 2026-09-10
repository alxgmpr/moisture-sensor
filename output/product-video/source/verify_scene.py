import bpy,json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
s=bpy.context.scene
objects=[o for o in s.objects if o.type in {'MESH','FONT'} and 'Seamless' not in o.name]
assert any(' / BT1 / ' in o.name for o in objects)
assert any(o.name.startswith('CR2032 | installed') for o in objects)
assert sum(' / U1 / ' in o.name for o in objects)==2
frames=[]
for f in range(1,194):
 s.frame_set(f);bpy.context.view_layer.update()
 points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
 uv=[world_to_camera_view(s,s.camera,p) for p in points]
 ext=[min(p.x for p in uv),max(p.x for p in uv),min(p.y for p in uv),max(p.y for p in uv)]
 assert ext[0]>.015 and ext[1]<.985 and ext[2]>.015 and ext[3]<.985,(f,ext)
 assert min(p.z for p in points)>-.0005,(f,'ground intersection')
 frames.append({'frame':f,'bounds_normalized':ext})
s.frame_set(1);a=bpy.data.objects['Turntable • full assembled PCB'].matrix_world.copy();s.frame_set(193);b=bpy.data.objects['Turntable • full assembled PCB'].matrix_world.copy()
assert max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))<1e-5
out={'holder_present':True,'cell_present':True,'DNP_U1_meshes':2,'all_frames_in_camera':True,'no_floor_intersection':True,'loop_end_matches_start':True,'frames':frames}
Path('output/product-video/animation-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='frames'})
