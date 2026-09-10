import bpy,json
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene
holder=next(o for o in s.objects if ' / BT1 / ' in o.name)
mesh=holder.data;mesh.calc_loop_triangles()
report={'vertices':[[c*1000 for c in v.co] for v in mesh.vertices],'faces':[list(t.vertices) for t in mesh.loop_triangles]}
Path(__file__).with_name('original-holder-mesh.json').write_text(json.dumps(report))
