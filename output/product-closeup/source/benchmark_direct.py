import bpy,time
from pathlib import Path
OUT=Path(__file__).resolve().parents[1];s=bpy.context.scene
s.render.resolution_x=2560;s.render.resolution_y=1440;s.render.resolution_percentage=100
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=64;s.eevee.use_raytracing=False
for f in [1,2]:
 s.frame_set(f);s.render.filepath=str(OUT/f'quality-direct-{f}.png');t=time.time();bpy.ops.render.render(write_still=True);print('SECONDS',time.time()-t,flush=True)
