import bpy,time
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
s=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=(d.type=='METAL')
s.cycles.device='GPU';s.render.use_persistent_data=True
s.render.resolution_percentage=100
s.render.resolution_x=1280;s.render.resolution_y=720;s.cycles.samples=16
s.render.filepath=str(OUT/"frames-hd"/"")
s["Notes"]="8-second seamless 360-degree studio rotation. Holder, installed CR2032 and DNP U1 included. 24 fps, 1280x720."
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"moisture-sensor-turntable.blend"))
for f in range(1,193):
 path=OUT/'frames-hd'/f'{f:04d}.png'
 if path.exists():continue
 start=time.time();s.frame_set(f);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 print('FRAME',f,'SECONDS',round(time.time()-start,2),flush=True)
