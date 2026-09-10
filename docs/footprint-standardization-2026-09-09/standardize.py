"""Use installed KiCad passive/DPY geometry while retaining board identity and nets."""
from pathlib import Path
import math
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools_export_bl54l15 import blocks
from tools_sexp import parse, find, first

LIB = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
BOARD = ROOT / 'nrf-moisture-sensor.kicad_pcb'
SCH = ROOT / 'nrf-moisture-sensor.kicad_sch'

def children(text):
    return [raw for _, _, raw in blocks(text)]

def key(raw):
    return parse(raw)[0]

def global_xy(local, origin, rotation):
    a = math.radians(rotation)
    x, y = map(float, local)
    return (round(origin[0] + x*math.cos(a) + y*math.sin(a), 6),
            round(origin[1] - x*math.sin(a) + y*math.cos(a), 6))

source = BOARD.read_text()
changes = {}
endpoints = {}
geometry = {'descr', 'tags', 'pad', 'model', 'zone', 'embedded_fonts',
            'duplicate_pad_numbers_are_jumpers'}
for start, end, raw in reversed(list(blocks(source))):
    if not raw.startswith('(footprint '):
        continue
    fp = parse(raw)
    props = {p[1]: p[2] for p in find(fp, 'property')}
    ref = props.get('Reference', '')
    if not re.fullmatch('[RCD][0-9]+', ref):
        continue
    if ref.startswith('R'):
        target = 'Resistor_SMD:R_0402_1005Metric'
    elif ref.startswith('D'):
        target = 'Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm'
    else:
        target = 'Capacitor_SMD:' + ('C_0603_1608Metric' if ref == 'C3' else 'C_0402_1005Metric')
    lib, name = target.split(':')
    template = (LIB / (lib + '.pretty') / (name + '.kicad_mod')).read_text()
    rotation = float(first(first(fp, 'transform'), 'rotate')[1])
    origin = list(map(float, first(first(fp, 'transform'), 'translate')[1:]))
    pads = {parse(p)[1]: p for p in children(raw) if key(p) == 'pad'}
    kept = [p for p in children(raw) if key(p) not in geometry and not key(p).startswith('fp_')]
    added = []
    for child in children(template):
        kind = key(child)
        if kind not in geometry and not kind.startswith('fp_'):
            continue
        child = re.sub(r'\(uuid "[^"]+"\)', lambda _: '(uuid "' + str(uuid.uuid4()) + '")', child)
        if kind in {'pad', 'fp_text'}:
            at = first(parse(child), 'at')
            angle = (float(at[3]) if len(at) > 3 else 0) + rotation
            child = re.sub(r'\(at [^)]*\)', f'(at {at[1]} {at[2]} {angle:g})', child, count=1)
        if kind == 'pad':
            node = parse(child)
            old = parse(pads[node[1]])
            old_xy = global_xy(first(old, 'at')[1:3], origin, rotation)
            new_xy = global_xy(first(node, 'at')[1:3], origin, rotation)
            if old_xy != new_xy:
                endpoints[old_xy] = new_xy
            child = re.sub(r'\s*\(uuid "[^"]+"\)', '', child)
            extra = [p for p in children(pads[node[1]]) if key(p) in {'net', 'pintype', 'pinfunction', 'uuid', 'teardrops'}]
            child = child[:-1] + '\n' + '\n'.join(extra) + '\n)'
        if kind == 'model' and ref.startswith('D'):
            # Installed KiCad footprint references an unavailable STEP file.
            # Retain the existing matching package model without changing lands.
            child = child.replace('${KICAD10_3DMODEL_DIR}/Package_SON.3dshapes/Texas_DPY0002A_0.6x1mm_P0.65mm.step',
                                  '${KIPRJMOD}/lib/TI_DPY0002A.step')
        added.append(child)
    replacement = '(footprint "' + target + '"\n' + '\n'.join(kept + added) + '\n)'
    source = source[:start] + replacement + source[end:]
    changes[ref] = (fp[1], target)

# Keep center-attached track ends centered when hand-solder pad centers shrink.
snapped = 0
for start, end, raw in reversed(list(blocks(source))):
    if not raw.startswith('(segment'):
        continue
    updated = raw
    for label in ('start', 'end'):
        point = first(parse(raw), label)
        if point and tuple(map(float, point[1:3])) in endpoints:
            xy = endpoints[tuple(map(float, point[1:3]))]
            updated = re.sub(r'\(' + label + r' [^)]*\)', f'({label} {xy[0]:g} {xy[1]:g})', updated, count=1)
            snapped += 1
    source = source[:start] + updated + source[end:]
BOARD.write_text(source)
schematic = SCH.read_text()
for old, new in set(changes.values()):
    schematic = schematic.replace('"' + old + '"', '"' + new + '"')
SCH.write_text(schematic)
print(f'Standardized {len(changes)} footprints; recentered {snapped} track ends.')
for ref, (old, new) in sorted(changes.items()):
    if old != new:
        print(f'{ref}: {new}')
