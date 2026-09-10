"""An ESD return via must land in GND copper, not a driven-shield region."""
import math
import unittest
from pathlib import Path
from tools_sexp import parse, find, first

ROOT = Path(__file__).resolve().parents[1]

def inside(point, polygon):
    x,y=point; odd=False
    for (x1,y1),(x2,y2) in zip(polygon,polygon[1:]+polygon[:1]):
        if (y1>y)!=(y2>y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1:
            odd=not odd
    return odd

class EsdReturnPlanes(unittest.TestCase):
    def test_probe_clamps_have_nearby_ground_vias_in_ground_plane(self):
        b=parse((ROOT/'nrf-moisture-sensor.kicad_pcb').read_text())
        ground=[]
        for z in find(b,'zone'):
            if first(z,'net') != ['net','GND']:continue
            for f in find(z,'filled_polygon'):
                if first(f,'layer')[1] not in ['In1.Cu','In2.Cu']:continue
                ground.append([tuple(map(float,p[1:3])) for p in find(first(f,'pts'),'xy')])
        vias=[tuple(map(float,first(v,'at')[1:3])) for v in find(b,'via') if first(v,'net')==['net','GND']]
        for ref in ['D8','D9']:
            f=next(f for f in find(b,'footprint') if ['property','Reference',ref] == next(p[:3] for p in find(f,'property') if p[1]=='Reference'))
            tr=first(f,'transform');x,y=map(float,first(tr,'translate')[1:3]);a=-math.radians(float(first(tr,'rotate')[1]))
            p=next(p for p in find(f,'pad') if first(p,'net')==['net','GND']);dx,dy=map(float,first(p,'at')[1:3])
            at=(x+dx*math.cos(a)-dy*math.sin(a),y+dx*math.sin(a)+dy*math.cos(a))
            local=[v for v in vias if math.dist(v,at)<=.7 and any(inside(v,g) for g in ground)]
            self.assertTrue(local, f'{ref}: no GND-plane via within 0.7 mm of clamp ground')
