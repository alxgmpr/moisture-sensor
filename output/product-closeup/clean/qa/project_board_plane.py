import bpy,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene
rig=bpy.data.objects['Turntable • full assembled PCB']
report={}
for f in range(215,245):
 s.frame_set(f)
 points=[]
 for x,y in [(-.02,.00),(.02,.00),(.02,.06),(-.02,.06)]:
  v=world_to_camera_view(s,s.camera,rig.matrix_world@Vector((x,y,.0087442)))
  points.append([v.x*2560,(1-v.y)*1440])
 report[f]=points
Path(__file__).with_name('board-plane.json').write_text(json.dumps(report))
