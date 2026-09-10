import bpy,json
from mathutils import Vector
from pathlib import Path
out=Path(__file__).resolve().parent
s=bpy.context.scene
holder=next(o for o in s.objects if ' / BT1 / ' in o.name)
for o in s.objects:
 if o.type in {'MESH','FONT'}:o.hide_render=(o!=holder)
rig=holder.parent;rig.animation_data_clear();rig.rotation_euler=(0,0,0)
bpy.context.view_layer.update()
report=[]
for idx,m in enumerate(holder.data.materials):
 n=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 vertices={v for p in holder.data.polygons if p.material_index==idx for v in p.vertices}
 points=[holder.matrix_local@holder.data.vertices[v].co for v in vertices]
 report.append({'index':idx,'name':m.name,'base_color':list(n.inputs['Base Color'].default_value) if n else None,'bounds':[[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]})
print(json.dumps(report,indent=2));(out/'holder-materials.json').write_text(json.dumps(report,indent=2))
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
s.render.resolution_x=1400;s.render.resolution_y=900;s.render.resolution_percentage=100
cam=s.camera;cam.animation_data_clear();cam.data.type='ORTHO';cam.data.ortho_scale=.040
center=Vector((0,.0346,.011))
for label,offset in [('top',(0,0,.1)),('side',(0,-.1,.015))]:
 cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=str(out/f'holder-{label}.png');bpy.ops.render.render(write_still=True)
