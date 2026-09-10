import cadquery as cq,json
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
a=cq.importers.importStep(str(OUT/'pcb-full.step')).val()
solids=a.Solids(); board=max(solids,key=lambda s:s.BoundingBox().ylen)
b=board.BoundingBox()
print('PCB STEP body bbox mm',b.xlen,b.ylen,b.zlen,b.zmin,b.zmax,flush=True)
case=cq.importers.importStep(str(OUT/'case-bottom-concept.step')).val()
# Reflection in width is harmless for this symmetric manufacturer's case; slots
# were authored with board +X along manufacturer +Z.
case=case.transformGeometry(cq.Matrix([[0,0,1,0],[-1,0,0,0],[0,1,0,0],[0,0,0,1]]))
board=board.translate((0,0,6.2))
volume=board.intersect(case).Volume()
report={'pcb_body_dimensions_mm':[b.xlen,b.ylen,b.zlen], 'pcb_body_vs_modified_case_intersection_mm3':volume,'scope':'PCB substrate against bottom case only; component and fastener fit not certified.'}
(OUT/'case-fit-check.json').write_text(json.dumps(report,indent=2));print(report)
