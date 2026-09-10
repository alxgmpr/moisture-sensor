"""Build editable, true-scale Blender product photography scenes from CAD."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(OUT/'pcb-full.glb'))
source=[]
audit=[]
for o in list(bpy.context.scene.objects):
    if o.type!='MESH': continue
    chain=[]; p=o
    while p: chain.append(p.name); p=p.parent
    mat=o.matrix_world.copy(); o.parent=None; o.matrix_world=mat
    o.name=' / '.join(reversed(chain))
    audit.append({'object':o.name,'dimensions_m':list(o.dimensions)})
    source.append(o)
for o in list(bpy.context.scene.objects):
    if o.type=='EMPTY': bpy.data.objects.remove(o,do_unlink=True)
assert any('U1' in o.name for o in source), 'DNP module missing'

def bump(mat,scale,distance,strength=.2):
    n=mat.node_tree.nodes; l=mat.node_tree.links; p=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=scale; tex.inputs['Detail'].default_value=2
    coords=n.new('ShaderNodeTexCoord'); l.new(coords.outputs['Object'],tex.inputs['Vector'])
    b=n.new('ShaderNodeBump'); b.inputs['Distance'].default_value=distance; b.inputs['Strength'].default_value=strength
    l.new(tex.outputs['Fac'],b.inputs['Height']); l.new(b.outputs['Normal'],p.inputs['Normal'])

def material(name,color,metal=0,rough=.4,texture=None):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    if texture: bump(m,*texture)
    return m
for m in list(bpy.data.materials):
    if not m.use_nodes: continue
    p=next((x for x in m.node_tree.nodes if x.type=='BSDF_PRINCIPLED'),None)
    if p is None: continue
    color=p.inputs['Base Color'].default_value[:3]; idx=int(m.name.split('_')[-1]) if m.name.startswith('mat_') else -1
    p.inputs['Alpha'].default_value=1
    if idx in [44,45]:
        m.name='Solder mask | deep forest satin'; p.inputs['Base Color'].default_value=(.013,.085,.035,1); p.inputs['Metallic'].default_value=0; p.inputs['Roughness'].default_value=.29
        p.inputs['Coat Weight'].default_value=.25; p.inputs['Coat Roughness'].default_value=.3
        bump(m,18000,.000004,.16)
    elif idx==46:
        m.name='FR4 | exposed laminate edge'; p.inputs['Base Color'].default_value=(.23,.25,.11,1); p.inputs['Roughness'].default_value=.6; bump(m,26000,.000015,.35)
    elif idx in [42,43]:
        m.name='Silkscreen | warm white epoxy'; p.inputs['Roughness'].default_value=.58
    elif idx in [40,41]:
        m.name='ENIG gold' if idx==40 else 'Solder | satin tin'; p.inputs['Metallic'].default_value=.95; p.inputs['Roughness'].default_value=.24
        if idx==40:p.inputs['Base Color'].default_value=(.72,.49,.16,1)
    elif max(color)<.2:
        p.inputs['Metallic'].default_value=0; p.inputs['Roughness'].default_value=.44
    elif max(color)-min(color)<.1 and max(color)>.3:
        p.inputs['Metallic'].default_value=.85; p.inputs['Roughness'].default_value=.27
    else:
        p.inputs['Metallic'].default_value=0; p.inputs['Roughness'].default_value=.4
poly=material('Hammond black polycarbonate | fine mold texture',(.016,.019,.023),rough=.35,texture=(11000,.000023,.28))
rubber=material('Gasket | black elastomer',(.006,.007,.008),rough=.73,texture=(10000,.000015,.2))
nickel=material('CR2032 | brushed nickel',(.58,.61,.65),.95,.26,texture=(30000,.000002,.1))
ink=material('Cell engraving | dark gray',(.06,.065,.07),.5,.45)
nylon=material('Fasteners | black nylon',(.018,.019,.02),0,.36)
base=material('Studio | warm mineral',(.26,.235,.205),rough=.77,texture=(900,.00009,.22))
case_data=json.loads((OUT/'case-meshes.json').read_text())
# Collect board meshes as a reusable linked assembly. glTF is metres, Z-up after import.
board_collection=bpy.context.scene.collection.children[0]
for o in source:
    for c in list(o.users_collection): c.objects.unlink(o)
# Cell model is a separate inferred installed CR2032 envelope, not manufacturer CAD.
def cylinder(name,radius,depth,loc,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=radius,depth=depth,location=loc)
    o=bpy.context.object; o.name=name; o.data.materials.append(mat)
    b=o.modifiers.new('Machined edge highlight','BEVEL'); b.width=.00010; b.segments=3
    for p in o.data.polygons: p.use_smooth=abs(p.normal.z)<.5
    return o

def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def light(scene,name,loc,power,size,color,target,shape='DISK',size_y=None):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape=shape; d.size=size; d.color=color
    if size_y and shape=='RECTANGLE':d.size_y=size_y
    o=bpy.data.objects.new(name,d); scene.collection.objects.link(o); o.location=loc; aim(o,target)

def studio(name,mode):
    s=bpy.data.scenes.new(name); bpy.context.window.scene=s
    s.unit_settings.system='METRIC'; s.unit_settings.length_unit='MILLIMETERS'
    s.render.engine='CYCLES'; s.cycles.samples=80; s.cycles.use_denoising=True
    s.cycles.max_bounces=8; s.render.threads_mode='FIXED'; s.render.threads=10
    s.render.resolution_x=1800; s.render.resolution_y=1400; s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGBA'
    s.world=bpy.data.worlds.new(name+' ambient'); s.world.use_nodes=True; s.world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.28,.34,1); s.world.node_tree.nodes['Background'].inputs[1].default_value=.28
    s.view_settings.view_transform='AgX'; s.view_settings.exposure=-2.7
    group=bpy.data.collections.new('PCB • DNP included'); s.collection.children.link(group)
    lift=.0062 if mode!='bare' else .0012
    if mode=='exploded':lift+=.012
    for original in source:
        o=original.copy(); o.data=original.data; group.objects.link(o); o.location.z+=lift
    cylinder('CR2032 | installed cell — nominal envelope',.010,.0032,(0,-.0054,lift+.0016+.00125+.0016),nickel)
    # A subtle inset rim and nominal markings establish scale without inventing a brand.
    cylinder('Cell top rim',.00965,.00010,(0,-.0054,lift+.0016+.00445),nickel)
    for label,size,dy in [('CR2032',.0022,.001),('3V  +',.0015,-.002)]:
        d=bpy.data.curves.new(label,'FONT'); d.body=label; d.size=size; d.align_x='CENTER'; d.extrude=.000001
        t=bpy.data.objects.new(label,d); s.collection.objects.link(t); t.location=(0,-.0054+dy,lift+.00612); t.data.materials.append(ink)
    if mode!='bare':
        c=bpy.data.collections.new('Hammond 1551WK • concept wall slots'); s.collection.children.link(c)
        for part,data in case_data.items():
            mesh=bpy.data.meshes.new(part); mesh.from_pydata(data['vertices'],[],data['faces']); mesh.update()
            o=bpy.data.objects.new('Hammond '+part,mesh); c.objects.link(o); mesh.materials.append(rubber if part=='Gasket' else poly)
            # Smooth small tessellation facets but keep actual mold edges crisp.
            for p in mesh.polygons:p.use_smooth=True
            mod=o.modifiers.new('Mold edge normals','WEIGHTED_NORMAL'); mod.keep_sharp=True; mod.weight=40
            if mode=='exploded':o.location.z={'Bottom':0,'Gasket':.031,'Lid':.045}[part]
        if mode=='closed':
            for x in [-.01575,.01575]:
                for y in [-.03575,.03575]:
                    cylinder('Case fastener | illustrative nylon',.00165,.001,(x,y,.0216),nylon)
    floorz=-.0005
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,floorz)); bpy.context.object.name='Seamless studio surface'; bpy.context.object.data.materials.append(base)
    target=(0,-.038,.006 if mode=='bare' else .012)
    loc=(.165,-.255,.245)
    if mode=='exploded':target=(0,-.028,.025);loc=(.20,-.28,.23)
    d=bpy.data.cameras.new('Product camera | 65 mm'); cam=bpy.data.objects.new('Product camera',d); s.collection.objects.link(cam); cam.location=loc;aim(cam,target);s.camera=cam;d.lens=65;d.clip_start=.001;d.clip_end=100
    d.dof.use_dof=True;d.dof.focus_distance=(Vector(target)-cam.location).length;d.dof.aperture_fstop=32
    light(s,'Key | large warm softbox',(-.11,-.04,.24),10,.19,(1,.90,.79),target,'RECTANGLE',.26)
    light(s,'Rim | cool strip',(.09,.06,.15),7,.07,(.75,.86,1),target,'RECTANGLE',.22)
    light(s,'Fill | front silk',(.02,-.21,.15),3,.15,(1,.97,.90),target)
    s['Notes']='True-scale PCB; DNP U1 included. Original Hammond STEP with proposed probe/sensor slots. CR2032 and fasteners are illustrative envelopes. See README.'
    return s
scenes=[studio('01 • Bare PCB','bare'),studio('02 • Enclosed product','closed'),studio('03 • Exploded assembly','exploded')]
# Additional closer composition, using the bare assembly.
s=scenes[0].copy();s.name='04 • Electronics detail';bpy.context.window.scene=s
cam=s.camera.copy();cam.data=s.camera.data.copy();s.collection.objects.link(cam);s.camera=cam
cam.location=(.069,-.075,.115);target=(0,.002,.005);aim(cam,target);cam.data.lens=60;cam.data.dof.focus_distance=(Vector(target)-cam.location).length;cam.data.dof.aperture_fstop=20
scenes.append(s)
# Remove unused staging scene and preserve all assets inside one .blend.
for old in list(bpy.data.scenes):
    if old not in scenes:bpy.data.scenes.remove(old)
for scene in scenes: scene.use_fake_user=True
bpy.context.window.scene=scenes[0]
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'; area.spaces.active.clip_start=.001
(OUT/'import-audit.json').write_text(json.dumps(audit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'moisture-sensor-studio.blend'))
for s,filename in zip(scenes,['01-bare-pcb.png','02-enclosed-product.png','03-exploded-assembly.png','04-electronics-detail.png']):
    bpy.context.window.scene=s;s.render.filepath=str(OUT/filename);bpy.ops.render.render(write_still=True)
bpy.context.window.scene=scenes[0];bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'moisture-sensor-studio.blend'))
