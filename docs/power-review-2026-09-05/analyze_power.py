#!/usr/bin/env python3
"""Read actual KiCad copper and sweep an IPC-2221 screening model; stdlib only.
This is NOT a field solver, IPC-2152 qualification or regulator simulation.
Usage: python3 docs/power-review-2026-09-05/analyze_power.py [board.kicad_pcb]
"""
import collections, csv, hashlib, json, math, pathlib, re, sys

OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parent.parent
BOARD = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else next(ROOT.glob('*.kicad_pcb'))

def parse(text):
    stack, root = [], None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+', text):
        if token == '(':
            node = []
            if stack: stack[-1].append(node)
            stack.append(node)
        elif token == ')': root = stack.pop()
        else: stack[-1].append(json.loads(token) if token.startswith('"') else token)
    return root

def children(node, tag): return [c for c in node if isinstance(c, list) and c and c[0] == tag]
def child(node, tag, default=None): return next(iter(children(node, tag)), default or [tag])
def val(node, tag, default=''): return (child(node, tag) + [default])[1]
def xy(node, tag): return tuple(map(float, child(node, tag)[1:3]))
def current(width, thickness, inner=False, rise=10):
    area_mil2 = width * thickness / .0254**2
    return (.024 if inner else .048) * rise**.44 * area_mil2**.725
def rise_at(amps, width, thickness, inner=False):
    return (amps / ((.024 if inner else .048) * (width*thickness/.0254**2)**.725))**(1/.44)
def resistance(length, width, thickness, temp=20):
    return .01724 * (1+.00393*(temp-20)) * (length/1000)/(width*thickness)

raw = BOARD.read_text()
b = parse(raw)
stackup = child(child(b, 'setup'), 'stackup')
copper = {x[1]:float(val(x,'thickness')) for x in children(stackup,'layer') if val(x,'type')=='copper'}
segments, vias, pads, zones = [], [], [], []
for s in children(b,'segment'):
    start,end=xy(s,'start'),xy(s,'end')
    w,layer=float(val(s,'width')),val(s,'layer')
    length=math.dist(start,end)
    segments.append(dict(net=val(s,'net'), layer=layer, width_mm=w,length_mm=length,start=start,end=end,
                         resistance_20C_ohm=resistance(length,w,copper[layer])))
assert not children(b,'arc'), 'Track arcs must be added to model before running'
for v in children(b,'via'):
    vias.append(dict(net=val(v,'net'),at=xy(v,'at'),diameter_mm=float(val(v,'size')),drill_mm=float(val(v,'drill'))))
for f in children(b,'footprint'):
    props={p[1]:p[2] for p in children(f,'property')}
    if children(f,'transform'):
        transform=child(f,'transform'); fx,fy=xy(transform,'translate'); angle=math.radians(float(val(transform,'rotate','0')))
        assert xy(transform,'scale') == (1.,1.), 'Nonunit footprint scale unsupported'
    else:
        fx,fy=xy(f,'at'); at=child(f,'at'); angle=math.radians(float(at[3]) if len(at)>3 else 0)
    for p in children(f,'pad'):
        px,py=xy(p,'at')
        pads.append(dict(ref=props.get('Reference'), value=props.get('Value'),pin=p[1],net=val(p,'net'),
                         at=(fx+px*math.cos(angle)+py*math.sin(angle),fy-px*math.sin(angle)+py*math.cos(angle)),
                         size=xy(p,'size'),layers=child(p,'layers')[1:]))
for z in children(b,'zone'):
    if children(z,'keepout'): continue
    fills=[]
    for p in children(z,'filled_polygon'):
        points=[tuple(map(float,x[1:3])) for x in children(child(p,'pts'),'xy')]
        fills.append(dict(layer=val(p,'layer'),points=points))
    zones.append(dict(net=val(z,'net'),layers=child(z,'layers')[1:] or child(z,'layer')[1:],
                      min_thickness_mm=val(z,'min_thickness'),connect_pads=child(z,'connect_pads')[1:],
                      thermal_bridge_width_mm=val(child(z,'fill'),'thermal_bridge_width'),fills=fills))

inventory=dict(board=BOARD.name,sha256=hashlib.sha256(raw.encode()).hexdigest(),copper_mm=copper,
               segments=segments,vias=vias,pads=pads,zones=zones)
(OUT/'copper-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
cuts={'+3V3':[56.5,60,83.64,94.97,95.93,97.0],'VBAT':[94,95,98,99.5],'/VBAT_RAW':[85,90,92.5],'/VINT':[96,96.5,97]}
with (OUT/'zone-cross-sections.csv').open('w') as f:
    writer=csv.writer(f);writer.writerow(['net','layer','y_mm','filled_interval_start_x_mm','filled_interval_end_x_mm','width_mm'])
    for z in zones:
        for y in cuts.get(z['net'],[]):
            for p in z['fills']:
                pts=p['points']
                xs=sorted(a[0]+(y-a[1])*(bb[0]-a[0])/(bb[1]-a[1]) for a,bb in zip(pts,pts[1:]+pts[:1]) if (a[1]<=y<bb[1] or bb[1]<=y<a[1]))
                for k in range(0,len(xs),2): writer.writerow([z['net'],p['layer'],y,xs[k],xs[k+1],xs[k+1]-xs[k]])
group=collections.defaultdict(list)
for s in segments: group[s['net'],s['layer'],s['width_mm']].append(s)
with (OUT/'trace-widths.csv').open('w') as f:
    writer=csv.writer(f)
    writer.writerow(['net','layer','width_mm','count','total_length_mm','sum_resistance_20C_ohm','IPC2221_10C_A'])
    for (net,layer,w),ss in sorted(group.items()):
        writer.writerow([net,layer,w,len(ss),sum(s['length_mm'] for s in ss),sum(s['resistance_20C_ohm'] for s in ss),current(w,copper[layer],layer.startswith('In'))])
with (OUT/'current-sweep.csv').open('w') as f:
    writer=csv.writer(f)
    writer.writerow(['layer','nominal_width_mm','width_scale','copper_scale','current_A','model_rise_C','drop_mV_per_10mm_at_60C'])
    for layer,w in sorted({(s['layer'],s['width_mm']) for s in segments}|{('In1.Cu',.25),('F.Cu',.1),('F.Cu',.25),('F.Cu',.5),('F.Cu',1.)}):
        for ws,ts in [(1,1),(.8,.8)]:
            for amps in [.001,.005,.01,.02,.05,.075,.1,.15,.2,.25,.5,1.]:
                writer.writerow([layer,w,ws,ts,amps,rise_at(amps,w*ws,copper[layer]*ts,layer.startswith('In')),1000*amps*resistance(10,w*ws,copper[layer]*ts,60)])
with (OUT/'via-sweep.csv').open('w') as f:
    writer=csv.writer(f)
    writer.writerow(['drill_mm','assumed_wall_um','barrel_resistance_60C_mohm','current_A','drop_mV','loss_mW'])
    for drill in sorted({v['drill_mm'] for v in vias}):
        for wall in [.012,.018,.025]:
            area=math.pi*((drill/2+wall)**2-(drill/2)**2)
            r=.01724*(1+.00393*40)*.0016/area
            for amps in [.01,.05,.1,.15,.25,.5,1.]: writer.writerow([drill,wall*1000,r*1000,amps,amps*r*1000,amps**2*r*1000])
print('Board:', BOARD.name, 'Copper:',copper)
for net in ['+3V3','VBAT','/VBAT_RAW','/VINT','/SW','GND']:
    ss=[s for s in segments if s['net']==net]
    print(net, 'segments',len(ss),'widths',sorted({s['width_mm'] for s in ss}),'sum R',sum(s['resistance_20C_ohm'] for s in ss))
    print('pads',[(p['ref'],p['pin'],p['at']) for p in pads if p['net']==net])
print('zones',[(z['net'],z['layers'],z['connect_pads'],len(z['fills'])) for z in zones])
