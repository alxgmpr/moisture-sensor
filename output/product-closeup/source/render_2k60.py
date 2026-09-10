import bpy,time,shutil,json
from pathlib import Path
OUT=Path(__file__).resolve().parents[1];s=bpy.context.scene;folder=OUT/'frames-2k60-final';folder.mkdir(parents=True,exist_ok=True)
assert (s.render.resolution_x,s.render.resolution_y,s.render.fps,s.frame_end)==(2560,1440,60,480)
for f in range(1,481):
 path=folder/f'{f:04d}.png'
 if path.exists():continue
 if f>451:
  # Exact static camera/scene hold: same rendered image, no interpolation.
  shutil.copyfile(folder/'0451.png',path);continue
 start=time.time();s.frame_set(f);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 print('FRAME',f,'SECONDS',round(time.time()-start,2),flush=True)
print('ALL_480_FRAMES_READY',flush=True)
