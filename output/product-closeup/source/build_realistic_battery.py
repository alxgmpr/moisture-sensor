"""Replace the nominal cell and unloaded holder contacts in the render scene."""
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[1]/'battery-realistic'
OUT.mkdir(exist_ok=True)
(OUT/'qa').mkdir(exist_ok=True)
s=bpy.context.scene
rig=bpy.data.objects['Turntable • full assembled PCB']
holder=next(o for o in s.objects if ' / BT1 / ' in o.name)
origin=holder.location.copy()
seat=1.45
for o in list(s.objects):
    if o.name.startswith('CR2032 | installed') or o.name in {'Cell top rim','CR2032','3V  +'}:
        bpy.data.objects.remove(o,do_unlink=True)

def material(name,color,metallic,roughness):
    m=bpy.data.materials.new(name)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic
    p.inputs['Roughness'].default_value=roughness
    m.diffuse_color=(*color,1)
    return m

face=material('Cell | satin nickel positive face',(.52,.55,.59),1,.23)
p=face.node_tree.nodes.get('Principled BSDF');p.inputs['Anisotropic'].default_value=.35
tex=face.node_tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=110;tex.inputs['Detail'].default_value=2
coords=face.node_tree.nodes.new('ShaderNodeTexCoord');face.node_tree.links.new(coords.outputs['Generated'],tex.inputs['Vector'])
ramp=face.node_tree.nodes.new('ShaderNodeMapRange');ramp.inputs['To Min'].default_value=.205;ramp.inputs['To Max'].default_value=.245
face.node_tree.links.new(tex.outputs['Fac'],ramp.inputs['Value']);face.node_tree.links.new(ramp.outputs['Result'],p.inputs['Roughness'])
rim=material('Cell | polished rolled nickel edge',(.62,.65,.69),1,.135)
side=material('Cell | drawn nickel sidewall',(.47,.50,.54),1,.21)
gasket=material('Cell | dark insulating gasket',(.018,.019,.020),0,.48)
mark=material('Cell | laser etched markings',(.075,.080,.085),.55,.4)
contact=material('Holder | installed plated spring contacts',(.50,.53,.56),1,.20)
plastic=material('Holder | ivory molded polymer',(.70,.70,.66),0,.32)
holder.data.materials[0]=contact
holder.data.materials[1]=plastic

# Clear the insertion well of the original unloaded spring tips. The source
# holder is an EasyEDA visualization substitute; this is an installed-state
# visualization edit, not a change to the PCB footprint or purchased part.
bpy.ops.mesh.primitive_cylinder_add(vertices=256,radius=.01004,depth=.008)
cutter=bpy.context.object;cutter.name='Temporary installed-cell clearance'
cutter.parent=rig;cutter.location=origin+Vector((0,0,(seat-.015+4)/1000))
bpy.context.view_layer.objects.active=holder
modifier=holder.modifiers.new('Installed-cell clearance','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
bpy.ops.object.modifier_apply(modifier=modifier.name)
bpy.data.objects.remove(cutter,do_unlink=True)

# Profiles below use millimetres and become meshes in the unchanged board rig.
def lathe(name,profile,materials,face_materials=None,z_offset=seat):
    count=256
    vertices=[(r*math.cos(2*math.pi*j/count)/1000,r*math.sin(2*math.pi*j/count)/1000,z/1000) for r,z in profile for j in range(count)]
    faces=[]
    for i in range(len(profile)):
        ni=(i+1)%len(profile)
        for j in range(count):faces.append((i*count+j,i*count+(j+1)%count,ni*count+(j+1)%count,ni*count+j))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    for m in materials:mesh.materials.append(m)
    if face_materials:
        for f in mesh.polygons:f.material_index=face_materials[f.index//count]
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-9)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free()
    for f in mesh.polygons:f.use_smooth=True
    o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);o.parent=rig;o.location=origin+Vector((0,0,z_offset/1000))
    return o

outer=[(0,3.18),(9.35,3.18),(9.60,3.16),(9.75,3.20),(9.90,3.14),(9.98,2.98),(10,2.85),(10,.45),(9.98,.32),(9.84,.16),(9.58,.10),(9.42,.18)]
can=lathe('CR2032 | installed positive can',outer+[(9.40,.35),(9.40,2.95),(0,2.95)],[face,rim,side],[0,0,1,1,1,1,2,1,1,1,1,1,2,0,0])
negative=lathe('Cell | negative underside',[(0,0),(8.9,0),(9.12,.035),(9.20,.12),(9.16,.22),(0,.22)],[side])
seal=lathe('Cell | insulating seal',[(9.18,.10),(9.25,.055),(9.39,.14),(9.43,.27),(9.34,.33),(9.20,.23)],[gasket])
envelope=lathe('Cell | verification envelope',[(0,0),(8.9,0),(9.12,.035),(9.25,.055),(9.42,.18)]+list(reversed(outer[:-1])),[gasket])
envelope.hide_render=True;envelope.hide_viewport=True

# The top electrode faces away from the PCB. Markings sit two micrometres above
# the face as laser-etched surface marks, without the old floating rim/text.
for text,size,y in [('+',.0030,.0046),('CR2032',.00245,.0011),('3 V',.0014,-.0018),('LITHIUM',.0009,-.0042)]:
    curve=bpy.data.curves.new('Cell marking '+text,'FONT');curve.body=text;curve.align_x='CENTER';curve.align_y='CENTER';curve.size=size;curve.extrude=0;curve.resolution_u=16
    obj=bpy.data.objects.new('Cell marking | '+text,curve);s.collection.objects.link(obj);obj.parent=rig;obj.location=origin+Vector((0,y,(seat+3.182)/1000));curve.materials.append(mark)

# Installed spring leaves: positive forks touch the outer area of the positive
# face; negative forks remain under the smaller negative underside electrode.
def leaf(name,path,y,width=1.05,thickness=.12):
    points=[]
    for i,(x,z) in enumerate(path):
        a=Vector(path[max(0,i-1)]);b=Vector(path[min(len(path)-1,i+1)])
        tangent=(b-a).normalized();normal=Vector((-tangent.y,tangent.x))*(thickness/2)
        for dy,sign in [(-width/2,-1),(width/2,-1),(width/2,1),(-width/2,1)]:
            points.append(((x+normal.x*sign)/1000,(y+dy)/1000,(z+normal.y*sign)/1000))
    faces=[(3,2,1,0)]
    for i in range(len(path)-1):
        for k in range(4):faces.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
    n=4*(len(path)-1);faces.append((n,n+1,n+2,n+3))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(points,[],faces);mesh.materials.append(contact)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(name,mesh);s.collection.objects.link(obj);obj.parent=rig;obj.location=origin
    bevel=obj.modifiers.new('Rounded stamped edges','BEVEL');bevel.width=.00002;bevel.segments=3
    return obj

leaves=[]
for y in [-1.30,1.30]:
    leaves.append(leaf('Holder | loaded positive fork', [(-11.35,4.50),(-10.50,4.88),(-9.85,4.88),(-9.0,4.80),(-8.6,4.70)],y))
    leaves.append(leaf('Holder | loaded negative fork', [(11.35,1.55),(10.50,1.35),(9.85,1.28),(8.5,1.38)],y))

# Export evaluated solids in holder coordinates for an independent volume test.
bpy.context.view_layer.update()
def export_mesh(o):
    evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
    transform=o.matrix_parent_inverse@o.matrix_basis
    data={'name':o.name,'vertices':[[float(v) for v in ((transform@p.co-origin)*1000)] for p in mesh.vertices],'faces':[list(t.vertices) for t in mesh.loop_triangles]}
    evaluated.to_mesh_clear();return data
report={'cell_envelope':export_mesh(envelope),'holder_parts':[export_mesh(o) for o in [holder]+leaves],'positive_face_outward':float((can.matrix_basis.to_3x3()@Vector((0,0,1))).z)>.999 and bpy.data.objects['Cell marking | +'].location.z>negative.location.z,'seat_above_holder_origin_mm':seat}
(OUT/'qa/installed-fit-meshes.json').write_text(json.dumps(report))
s.cycles.denoising_use_gpu=True
s.frame_start=1;s.frame_end=480;s.frame_set(1)
s.render.filepath=str(OUT/'frames')+'/'
s['Battery revision']='20 x 3.2 mm CR2032, marked positive face outward, formed nickel can with rolled edge and underside gasket. Holder insertion well and spring leaves model an installed cell. Visualization only; original KiCad/BOM unchanged.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'moisture-sensor-realistic-battery-2k60.blend'))
print('BATTERY_SCENE_BUILT',flush=True)
