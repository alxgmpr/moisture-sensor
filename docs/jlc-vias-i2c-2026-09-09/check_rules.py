"""Inject out-of-limit geometry into a disposable board; never edit the source PCB."""
from pathlib import Path
import json,re,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'injected'
OUT.mkdir(exist_ok=True)
base='nrf-moisture-sensor'
s=(ROOT/(base+'.kicad_pcb')).read_text()
counts={}
def change(m):
    t=m.group()
    if '2728878b-a7cc-4541-829c-f10a89de9e58' in t:
        counts['ring']=1
        return t.replace('(size 0.5)','(size 0.48)')
    if '405a1fe4-b761-4205-8737-eda755cd271a' in t:
        counts['gap']=1
        return t.replace('102.69','102.63')
    return t
s=re.sub(r'^\t\((?:via|segment)\n.*?^\t\)',change,s,flags=re.M|re.S)
# Reclassify one thermal via as an ordinary drilled pad to prove the exemption
# is specific to U2.17, and ordinary pads still get the stronger 0.30 mm rule.
def pad(m):
    t=m.group()
    if 'e7e125f1-7ee4-4dcb-976d-462f21788c2e' in t:
        counts['pad']=1
        return t.replace('(pad "17"','(pad "18"',1)
    return t
s=re.sub(r'^\t\t\(pad .*?^\t\t\)',pad,s,flags=re.M|re.S)
assert counts=={'ring':1,'gap':1,'pad':1},counts
(OUT/(base+'.kicad_pcb')).write_text(s)
for ext in ['kicad_pro','kicad_dru']:shutil.copy2(ROOT/(base+'.'+ext),OUT/(base+'.'+ext))
subprocess.run(['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(OUT/'drc.json'),str(OUT/(base+'.kicad_pcb'))],check=True,capture_output=True)
r=json.loads((OUT/'drc.json').read_text())
checks={
 'undersized_ring_rejected':any(v['type']=='annular_width' and '0.1000' in v['description'] and any(i['uuid']=='2728878b-a7cc-4541-829c-f10a89de9e58' for i in v['items']) for v in r['violations']),
 'tight_via_gap_rejected':any(v['type']=='hole_clearance' and '0.2000' in v['description'] and any(i['uuid']=='405a1fe4-b761-4205-8737-eda755cd271a' for i in v['items']) for v in r['violations']),
 'ordinary_pad_keeps_stricter_gap':any(v['type']=='hole_clearance' and 'JLC plated pad hole to copper' in v['description'] and any(i['uuid']=='e7e125f1-7ee4-4dcb-976d-462f21788c2e' for i in v['items']) for v in r['violations']),
}
print(json.dumps(checks,indent=2));(OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
assert all(checks.values()),checks
