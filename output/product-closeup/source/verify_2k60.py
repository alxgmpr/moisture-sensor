import bpy,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene;OUT=Path(__file__).resolve().parents[1]
assert (s.render.resolution_x,s.render.resolution_y,s.render.fps,s.frame_end)==(2560,1440,60,480)
objects=[o for o in s.objects if o.type in {'MESH','FONT'} and 'Seamless' not in o.name]
assert any(' / BT1 / ' in o.name for o in objects)
assert any(o.name.startswith('CR2032 | installed') for o in objects)
assert sum(' / U1 / ' in o.name for o in objects)==2
components=[o for o in objects if o.type=='FONT' or any((' / '+ref+' / ') in o.name for ref in ['BT1','U1','U2','U3','U4','Q1','L10']) or o.name.startswith('CR2032 | installed')]
report=[]
for f in range(1,481):
 s.frame_set(f);bpy.context.view_layer.update()
 sample=objects if f>=451 else components
 uv=[world_to_camera_view(s,s.camera,o.matrix_world@Vector(c)) for o in sample for c in o.bound_box]
 bounds=[min(p.x for p in uv),max(p.x for p in uv),min(p.y for p in uv),max(p.y for p in uv)]
 assert bounds[0]>.01 and bounds[1]<.99 and bounds[2]>.01 and bounds[3]<.99,(f,bounds)
 report.append({'frame':f,'camera_location':list(s.camera.location),'checked_bounds':bounds})
(OUT/'animation-audit.json').write_text(json.dumps({'resolution':[2560,1440],'fps':60,'frames':480,'duration_s':8,'holder_and_cell_retained':True,'DNP_U1_retained':True,'closeup_components_in_frame':True,'whole_board_in_final_frame':True,'camera_frames':report},indent=2))
print('PASSED: native 1440p60, retained components, framing of components, full-board ending.')
