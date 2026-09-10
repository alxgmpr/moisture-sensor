import bpy,json
from mathutils import Vector
from pathlib import Path
s=bpy.data.scenes['01 • Bare PCB'];results=[]
for o in s.objects:
 if o.type!='MESH' or 'Seamless' in o.name:continue
 pts=[o.matrix_world@Vector(v) for v in o.bound_box]
 results.append({'name':o.name,'z_min_mm':min(v.z for v in pts)*1000-1.2,'z_max_mm':max(v.z for v in pts)*1000-1.2})
results.sort(key=lambda r:-r['z_max_mm'])
Path('output/product-video/height-audit.json').write_text(json.dumps(results,indent=2)); print(results[:12])
