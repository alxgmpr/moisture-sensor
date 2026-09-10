import bpy,time
from pathlib import Path
OUT=Path(__file__).resolve().parents[1];s=bpy.context.scene
s.render.resolution_x=2560;s.render.resolution_y=1440;s.render.resolution_percentage=100
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.adaptive_threshold=.035;s.render.use_persistent_data=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=(d.type=='METAL')
s.cycles.device='GPU'
for f in [1,2]:
 s.frame_set(f);s.render.filepath=str(OUT/f'quality-cycles-{f}.png');t=time.time();bpy.ops.render.render(write_still=True);print('SECONDS',time.time()-t,flush=True)
