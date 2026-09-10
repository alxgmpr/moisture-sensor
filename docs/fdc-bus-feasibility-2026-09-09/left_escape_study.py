from pathlib import Path
import re,shutil,uuid,subprocess,json
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'left-study';OUT.mkdir(exist_ok=True)
base='nrf-moisture-sensor';s=(ROOT/(base+'.kicad_pcb')).read_text();added=[]
def segment(a,b,layer,net):
 u=str(uuid.uuid4());added.append(u);return f'(segment (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (width 0.2) (layer "{layer}") (net "{net}") (uuid "{u}"))'
def via(x,y,net):
 u=str(uuid.uuid4());added.append(u);return f'(via (at {x} {y}) (size 0.5) (drill 0.3) (layers "F.Cu" "B.Cu") (net "{net}") (uuid "{u}"))'
items=[]
for y,pin,pad in [(52.7,'09','29'),(51.95,'08','30')]:
 net=f'unconnected-(U1-P1.{pin}-Pad{pad})'
 items += [segment((72.503,y),(71.4,y),'F.Cu',net),via(71.4,y,net),segment((71.4,y),(70.4,y),'B.Cu',net)]
s=s.rstrip()[:-1]+'\n'+'\n'.join(items)+'\n)\n';(OUT/(base+'.kicad_pcb')).write_text(s)
for e in ['kicad_pro','kicad_dru']:shutil.copy2(ROOT/(base+'.'+e),OUT/(base+'.'+e))
subprocess.run(['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli','pcb','drc','--refill-zones','--all-track-errors','--severity-all','--format','json','-o',str(OUT/'drc.json'),str(OUT/(base+'.kicad_pcb'))],check=True,capture_output=True)
r=json.loads((OUT/'drc.json').read_text());v=[v for v in r['violations'] if any(i['uuid'] in added for i in v['items'])];print(json.dumps(v,indent=2));(OUT/'new-item-violations.json').write_text(json.dumps(v,indent=2)+'\n')
