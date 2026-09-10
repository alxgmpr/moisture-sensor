import bpy
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
for s in sorted(bpy.data.scenes,key=lambda s:s.name):
 bpy.context.window.scene=s
 s.render.resolution_percentage=100
 s.cycles.samples=64
 name={'01':'01-bare-pcb.png','02':'02-enclosed-product.png','03':'03-exploded-assembly.png','04':'04-electronics-detail.png'}[s.name[:2]]
 s.render.filepath=str(OUT/name)
 bpy.ops.render.render(write_still=True)
bpy.context.window.scene=bpy.data.scenes['01 • Bare PCB']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'moisture-sensor-studio.blend'))
