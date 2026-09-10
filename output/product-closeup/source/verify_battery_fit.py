"""Solid-volume interference test on Blender-exported geometry, in millimetres."""
import json
import sys
from pathlib import Path
import trimesh

path=Path(sys.argv[1])
r=json.loads(path.read_text())
def mesh(part):
    m=trimesh.Trimesh(part['vertices'],part['faces'])
    m.merge_vertices(digits_vertex=5)
    assert m.is_watertight and m.is_winding_consistent and m.volume>0, part.get('name','mesh')
    return m
cell=mesh(r['cell_envelope'])
assert abs(cell.extents[0]-20)<.01 and abs(cell.extents[1]-20)<.01 and abs(cell.extents[2]-3.2)<.01, cell.extents
report=[]
for p in r['holder_parts']:
    h=mesh(p)
    intersection=trimesh.boolean.intersection([h,cell],engine='manifold')
    volume=0.0 if intersection.is_empty else abs(float(intersection.volume))
    report.append({'part':p['name'],'intersection_mm3':volume})
result={'cell_dimensions_mm':cell.extents.tolist(),'intersections':report,'positive_face_outward':r['positive_face_outward']}
path.with_name(path.stem+'-fit-report.json').write_text(json.dumps(result,indent=2))
assert r['positive_face_outward'], 'Positive face must point outward from the PCB'
assert all(p['intersection_mm3']<.001 for p in report), report
print(json.dumps({'passed':True,**result},indent=2))
