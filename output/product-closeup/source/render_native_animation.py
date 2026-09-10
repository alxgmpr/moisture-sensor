import bpy,shutil,time
from pathlib import Path
OUT=Path(__file__).resolve().parents[1];folder=OUT/'frames-2k60-final';folder.mkdir(exist_ok=True)
s=bpy.context.scene
missing=[f for f in range(1,452) if not (folder/f'{f:04d}.png').exists()]
if missing:
 s.frame_start=min(missing);s.frame_end=451;s.render.filepath=str(folder)+'/'
 s.render.use_overwrite=False
 print('RENDER_START',s.frame_start,flush=True)
 bpy.ops.render.render(animation=True)
for f in range(452,481):shutil.copyfile(folder/'0451.png',folder/f'{f:04d}.png')
print('ALL_480_FRAMES_READY',flush=True)
