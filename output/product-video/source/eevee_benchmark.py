import bpy,time
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU'
s.render.engine='CYCLES' if not hasattr(bpy.types.Scene,'eevee') else 'CYCLES'
try:s.render.engine='BLENDER_EEVEE'
except TypeError:s.render.engine='BLENDER_EEVEE_NEXT'
s.eevee.taa_render_samples=64
s.eevee.use_raytracing=True
s.render.filepath='output/product-video/eevee-preview.png';start=time.time();bpy.ops.render.render(write_still=True);print('BENCHMARK',time.time()-start,flush=True)
s.render.filepath='output/product-video/eevee-preview-2.png';s.frame_set(49);start=time.time();bpy.ops.render.render(write_still=True);print('BENCHMARK',time.time()-start,flush=True)
