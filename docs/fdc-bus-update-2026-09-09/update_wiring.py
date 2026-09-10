"""One-time, targeted edit from the saved pre-change design. Leaves routing to user."""
from pathlib import Path
import re,uuid,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools_sexp import parse,first,find
D=Path(__file__).resolve().parent
UID=lambda:str(uuid.uuid4())
def nodes(s):
 depth=0;start=0
 for m in re.finditer(r'"(?:[^"\\]|\\.)*"|[()]',s):
  if m.group()=='(':
   if depth==1:start=m.start()
   depth+=1
  elif m.group()==')':
   depth-=1
   if depth==1:yield start,m.end(),s[start:m.end()]
def ref(n):
 return next((p[2] for p in find(n,'property') if p[1]=='Reference'),None)
def newids(s):return re.sub(r'\(uuid "[^"]+"\)',lambda m:f'(uuid "{UID()}")',s)
def move(s,dx,dy):
 return re.sub(r'\(at ([\d.-]+) ([\d.-]+)',lambda m:f'(at {float(m[1])+dx:.4f} {float(m[2])+dy:.4f}',s)
def wire(a,b):return f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid "{UID()}"))'
def label(name,x,y):return f'(label "{name}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{UID()}"))'
s=(D/'before/nrf-moisture-sensor.kicad_sch').read_text(); edits=[];add=[]; sym={ref(parse(t)):t for _,_,t in nodes(s) if parse(t)[0]=='symbol'}
for a,b,t in nodes(s):
 n=parse(t)
 if n[0]=='no_connect' and tuple(map(float,first(n,'at')[1:3])) in [(134.62,66.04),(134.62,68.58)]:edits.append((a,b,''))
 if n[0]=='label' and n[1] in ['SDA','SCL'] and float(first(n,'at')[1])==398.78:edits.append((a,b,t.replace(f'"{n[1]}"',f'"FDC_{n[1]}"',1)))
for a,b,t in nodes(s):
 n=parse(t)
 if n[0]=='symbol' and first(n,'lib_id')[1]=='power_local:+3V3_FDC_SW' and tuple(map(float,first(n,'at')[1:3]))==(398.78,233.68):edits.append((a,b,move(t,-2.54,0)))
 if n[0]=='wire' and '(xy 398.7800 233.6800)' in t:edits.append((a,b,t.replace('(xy 398.7800 233.6800)','(xy 396.2400 233.6800)')))
for name,y in [('FDC_SDA',66.04),('FDC_SCL',68.58)]:add += [wire((134.62,y),(139.7,y)),label(name,139.7,y)]
# Use standard small US resistor symbol for the new pull-ups.
lib=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Device.kicad_sym').read_text()
rs=next(t for _,_,t in nodes(lib) if parse(t)[:2]==['symbol','R_Small_US']).replace('(symbol "R_Small_US"','(symbol "Device:R_Small_US"',1)
a,b,t=next(v for v in nodes(s) if parse(v[2])[0]=='lib_symbols');edits.append((a,b,t[:-1]+rs+'\n)'))
ids={}
for r,x,net,end in [('R36',419.10,'FDC_SDA',241.30),('R37',406.40,'FDC_SCL',238.76)]:
 t=newids(move(sym['R22'],x-368.3,228.6-266.7)).replace('"R22"',f'"{r}"').replace('"4.7k to +3V3"','"4.7kR"').replace('"Device:R_Small"','"Device:R_Small_US"')
 # Place reference/value beside resistor, clear of vertical wires.
 for pname,y in [('Reference',227.33),('Value',229.87)]:
  t=re.sub(r'(\(property "'+pname+r'" "[^"]+"\s*\(at) [\d.-]+ [\d.-]+',rf'\g<1> {x+2.54} {y}',t)
 ids[r]=first(parse(t),'uuid')[1];add.append(t)
 add += [wire((x,226.06),(x,222.25)),wire((x,231.14),(x,end)),wire((398.78,end),(x,end))]
add += [wire((406.4,222.25),(412.75,222.25)),wire((412.75,222.25),(419.1,222.25)),f'(junction (at 412.75 222.25) (diameter 0) (color 0 0 0 0) (uuid "{UID()}"))']
pwr=newids(move(sym['#PWR075'],412.75-340.36,222.25-259.08)).replace('"#PWR075"','"#PWR110"');assert '#PWR110' not in s;add.append(pwr)
for a,b,t in sorted(edits,reverse=True):s=s[:a]+t+s[b:]
s=s.rstrip()[:-1]+'\n'+'\n'.join(add)+'\n)\n';(ROOT/'nrf-moisture-sensor.kicad_sch').write_text(s)
# Update pad nets and remove only the FDC-only shared bus spurs.
p=(D/'before/nrf-moisture-sensor.kicad_pcb').read_text();edits=[];add=[];removed=[]
for a,b,t in nodes(p):
 n=parse(t)
 if n[0]=='footprint' and ref(n)=='U1':
  t=t.replace('unconnected-(U1-P1.05-Pad22)','/FDC_SDA').replace('unconnected-(U1-P1.04-Pad23)','/FDC_SCL');edits.append((a,b,t))
 if n[0]=='footprint' and ref(n)=='U3':edits.append((a,b,t.replace('(net "/SDA")','(net "/FDC_SDA")').replace('(net "/SCL")','(net "/FDC_SCL")')))
 if n[0]=='segment' and first(n,'net')[1] in ['/SDA','/SCL'] and first(n,'layer')[1]=='F.Cu':
  # These five segments lie exclusively between the branch vias and FDC pads.
  points={tuple(map(float,first(n,k)[1:])) for k in ['start','end']}
  expected=[{(68.175,102.2),(70,104.025)},{(70,104.025),(70,104.91)},{(68.825,101.8),(70.402,103.377)},{(70.402,103.377),(70.402,104.812)},{(70.402,104.812),(70.5,104.91)}]
  if points in expected:edits.append((a,b,''));removed.append(first(n,'uuid')[1])
assert len(removed)==5,removed
fp=next(t for _,_,t in nodes(p) if parse(t)[0]=='footprint' and ref(parse(t))=='R22')
for r,x,net in [('R36',75.0,'/FDC_SDA'),('R37',77.0,'/FDC_SCL')]:
 t=newids(fp).replace('"R22"',f'"{r}"').replace('"4.7k to +3V3"','"4.7kR"').replace('(translate 71.025 54.1)',f'(translate {x} 103.7)').replace('(net "+3V3")','(net "+3V3_FDC_SW")').replace('(net "/SDA")',f'(net "{net}")')
 t=re.sub(r'\(path "[^"]+"\)',f'(path "/{ids[r]}")',t);add.append(t)
for a,b,t in sorted(edits,reverse=True):p=p[:a]+t+p[b:]
p=p.rstrip()[:-1]+'\n'+'\n'.join(add)+'\n)\n';(ROOT/'nrf-moisture-sensor.kicad_pcb').write_text(p)
print('Added R36/R37; removed five FDC branch segments; no tracks added.')
