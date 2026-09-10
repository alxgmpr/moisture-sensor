import bpy
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
for s in bpy.data.scenes:
 s.view_settings.exposure=-2.7
 s.camera.data.dof.aperture_fstop=20 if s.name.startswith('04') else 32
 s.cycles.samples=64
 s.render.resolution_percentage=100
bpy.context.window.scene=bpy.data.scenes['01 • Bare PCB']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'moisture-sensor-studio.blend'))
s=bpy.context.scene;s.render.resolution_percentage=50;s.cycles.samples=24;s.render.filepath=str(OUT/'preview.png');bpy.ops.render.render(write_still=True)
