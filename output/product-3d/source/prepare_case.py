"""Tessellate manufacturer STEP parts; add concept wall slots for the real PCB."""
import json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/product-3d'
result={}
for name in ['Bottom','Lid','Gasket']:
    shape=cq.importers.importStep(str(ROOT/f'lib/enclosure/1551WK_{name}.stp')).val()
    if name=='Bottom':
        # STEP axes: X=board length, Y=height, Z=board width, all mm.
        probe=cq.Workplane('XY').box(8,2.3,20.8).translate((39,7.0,0)).val()
        sensor=cq.Workplane('XY').box(5.8,2.3,8).translate((-16.4,7.0,19)).val()
        shape=shape.cut(probe).cut(sensor)
        cq.exporters.export(shape,str(OUT/'case-bottom-concept.step'))
    vertices,faces=shape.tessellate(0.025,0.12)
    result[name]={'vertices':[[v.z/1000,-v.x/1000,v.y/1000] for v in vertices], 'faces':faces}
(OUT/'case-meshes.json').write_text(json.dumps(result))
print({k:(len(v['vertices']),len(v['faces'])) for k,v in result.items()})
