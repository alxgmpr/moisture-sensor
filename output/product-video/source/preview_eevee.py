import bpy,time
from pathlib import Path
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.render.resolution_percentage=50
s.render.filepath=str(Path('output/product-video/poster-preview.png').resolve());bpy.ops.render.render(write_still=True)
