"""Render the KiCad GLB with Blender Cycles; run from the repository root.
Export first using the command in docs/images/README.md.
blender --background --threads 4 --python scripts/render_pcb.py -- --preview
"""
import bpy
import math
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
preview = '--preview' in sys.argv
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'output/pcb-render/board.glb'))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
holder_meshes = [o for o in bpy.data.objects['BT1'].children_recursive if o.type == 'MESH']
# Bake world transforms, then scale meters to convenient studio units.
module = bpy.data.objects.get('U1')
module_pos = module.matrix_world.translation.copy() * 100
for obj in meshes:
    matrix = obj.matrix_world.copy()
    obj.parent = None
    obj.matrix_world = matrix
    obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for obj in meshes:
    for v in obj.data.vertices:
        v.co *= 100
bpy.context.view_layer.update()
points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in points) for i in range(3)])
hi = Vector([max(p[i] for p in points) for i in range(3)])
center = (lo + hi) / 2
print('BOARD BOUNDS',lo,hi,'MCU',module_pos)
for mat in bpy.data.materials:
    if not mat.use_nodes: continue
    bs = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'),None)
    if not bs: continue
    color = tuple(bs.inputs['Base Color'].default_value)
    alpha = bs.inputs['Alpha'].default_value
    bs.inputs['Alpha'].default_value = 1
    bs.inputs['Roughness'].default_value = .38
    if .80 < alpha < .85:
        bs.inputs['Base Color'].default_value = (.008,.065,.023,1)
        bs.inputs['Roughness'].default_value = .38
        bs.inputs['Coat Weight'].default_value = .08
        bs.inputs['Specular IOR Level'].default_value = .3
        noise = mat.node_tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 650
        noise.inputs['Detail'].default_value = 2
        bump = mat.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .16
        bump.inputs['Distance'].default_value = .003
        mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    elif alpha > .99 and min(color[:3]) > .3 and max(color[:3])-min(color[:3]) < .22:
        bs.inputs['Metallic'].default_value = .85
        bs.inputs['Roughness'].default_value = .24
    elif .88 < alpha < .92:
        bs.inputs['Base Color'].default_value = (.9,.93,.87,1)
        bs.inputs['Roughness'].default_value = .52
    elif max(color[:3]) < .12:
        bs.inputs['Roughness'].default_value = .48

# The supplier model assigns separate materials to contacts and molded housing.
# Override only BT1, retaining the black molded markings.
for obj in holder_meshes:
    for slot in obj.material_slots:
        original = slot.material
        if original.name not in ('mat_16', 'mat_17'):
            continue
        mat = original.copy()
        slot.material = mat
        bs = mat.node_tree.nodes['Principled BSDF']
        plastic = original.name == 'mat_17'
        mat.name = 'BT1 white molded plastic' if plastic else 'BT1 plated contacts'
        bs.inputs['Base Color'].default_value = (.82,.83,.80,1) if plastic else (.55,.58,.62,1)
        bs.inputs['Metallic'].default_value = 0 if plastic else 1
        bs.inputs['Roughness'].default_value = .34 if plastic else .22
        if plastic:
            noise = mat.node_tree.nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 500
            bump = mat.node_tree.nodes.new('ShaderNodeBump')
            bump.inputs['Strength'].default_value = .1
            bump.inputs['Distance'].default_value = .002
            mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
            mat.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24 if preview else 96
scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = .025
scene.cycles.time_limit = 240
scene.cycles.max_bounces = 8
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.resolution_x = 1200 if preview else 2400
scene.render.resolution_y = 900 if preview else 1800
scene.render.resolution_percentage = 100
scene.world.color = (.10,.10,.10)
scene.view_settings.exposure = 0
scene.view_settings.view_transform = 'AgX'

bpy.ops.mesh.primitive_plane_add(size=200, location=(center.x,center.y,lo.z-.025))
floor = bpy.context.object
floor.name = 'Studio surface'
mat = bpy.data.materials.new('Warm porcelain backdrop')
mat.diffuse_color = (.68,.71,.70,1)
mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.68,.71,.70,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8
floor.data.materials.append(mat)

long = Vector((module_pos.x-center.x,module_pos.y-center.y,0)).normalized()
side = Vector((-long.y,long.x,0))
span = max(hi.x-lo.x,hi.y-lo.y)
target = center + long * span * .03
bpy.ops.object.camera_add(location=target + (long*.85+side*.85+Vector((0,0,1.05)))*span)
cam = bpy.context.object
cam.rotation_euler = (target-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type = 'PERSP'
cam.data.lens = 48
cam.data.ortho_scale = span * 1.1
cam.data.clip_end = 1000
scene.camera = cam

def area(name, offset, power, size, color):
    bpy.ops.object.light_add(type='AREA',location=center+Vector(offset)*span)
    obj=bpy.context.object;obj.name=name;obj.data.energy=power
    obj.data.shape='DISK';obj.data.size=size*span;obj.data.color=color
    obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
area('Large softbox',(-.6,-.5,1.5),3000,.8,(1,.95,.86))
area('Cool fill',(.9,.4,.8),800,.8,(.8,.9,1))
area('Edge strip',(-.1,1,.6),1800,.6,(1,1,1))
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(ROOT / ('output/pcb-render/preview.png' if preview else 'docs/images/pcb-three-quarter.png'))
if not preview: bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'output/pcb-render/moisture-sensor.blend'))
bpy.ops.render.render(write_still=True)
