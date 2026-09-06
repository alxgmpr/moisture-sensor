#!/usr/bin/env python3
"""Export a coherent JLC quote package from the maintained KiCad sources."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from tools_export_bl54l15 import blocks
from tools_sexp import parse, first

ROOT = Path(__file__).resolve().parent
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
STEM = 'nrf-moisture-sensor'
OUT = ROOT / 'production/jlc-economic-quote'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    checks = OUT / 'checks'
    checks.mkdir(exist_ok=True)
    board = ROOT / f'{STEM}.kicad_pcb'
    sch = ROOT / f'{STEM}.kicad_sch'
    log = []
    def run(*args):
        result = subprocess.run([CLI, *map(str,args)], cwd=ROOT, capture_output=True, text=True, check=True)
        log.append({'args':list(map(str,args)), 'stdout':result.stdout, 'stderr':result.stderr})
        print(result.stdout.strip(), flush=True)
    run('pcb','drc','--refill-zones','--save-board','--schematic-parity','--format','json','--output',checks/'drc.json',board)
    drc = json.loads((checks/'drc.json').read_text())
    assert not [x for x in drc['violations'] if x['severity']=='error'], 'DRC errors block export'
    assert not drc['unconnected_items'] and not drc['schematic_parity'], 'Connectivity/parity blocks export'
    run('sch','erc','--format','json','--output',checks/'erc.json',sch)
    erc = json.loads((checks/'erc.json').read_text())
    assert not [x for sheet in erc['sheets'] for x in sheet['violations'] if x['severity']=='error'], 'ERC errors block export'
    # Native schematic fields are authoritative. No procurement joins or substitutions.
    run('sch','export','bom','--exclude-dnp','--fields','Value,Reference,Footprint,LCSC',
        '--labels','Comment,Designator,Footprint,LCSC Part #','--group-by','Value,Footprint,LCSC',
        '--ref-range-delimiter','','--output',OUT/'JLC-BOM.csv',sch)
    rows=list(csv.DictReader((OUT/'JLC-BOM.csv').open()))
    assert all(r['LCSC Part #'] for r in rows), 'Missing LCSC code'
    refs={ref.strip() for row in rows for ref in row['Designator'].split(',')}
    assert 'U1' not in refs and 'BT1' in refs
    run('pcb','export','pos','--exclude-dnp','--format','csv','--units','mm','--side','both','--output',checks/'positions-kicad.csv',board)
    positions=list(csv.DictReader((checks/'positions-kicad.csv').open()))
    assert refs == {r['Ref'] for r in positions}, 'BOM/CPL reference mismatch'
    subprocess.run([sys.executable,'/Users/alex/.agents/skills/kicad-export/scripts/convert_position.py',str(checks/'positions-kicad.csv'),str(OUT/'JLC-CPL.csv')],check=True)
    gerbers=OUT/'gerbers'
    gerbers.mkdir(exist_ok=True)
    run('pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts','--subtract-soldermask','--output',str(gerbers)+'/',board)
    run('pcb','export','drill','--format','excellon','--excellon-separate-th','--output',str(gerbers)+'/',board)
    # Omit U1 paste while retaining its copper and soldermask for hand fitting.
    source=board.read_text()
    for a,z,b in reversed(list(blocks(source))):
        if b.startswith('(footprint') and 'dnp' in (first(parse(b),'attr') or []):
            source=source[:a]+source[z:]
    paste=checks/f'{STEM}.kicad_pcb'
    paste.write_text(source)
    run('pcb','export','gerbers','--layers','F.Paste,B.Paste','--output',str(gerbers)+'/',paste)
    with zipfile.ZipFile(OUT/'JLC-Gerbers.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(gerbers.iterdir()):
            if file.suffix.lower() in {'.gtl','.g1','.g2','.gbl','.gto','.gbo','.gts','.gbs','.gm1','.gtp','.gbp','.drl'}:archive.write(file,file.name)
    with zipfile.ZipFile(OUT/'JLC-Gerbers.zip') as archive:
        assert len(archive.namelist()) == 13, 'Expected 4 copper, 2 mask, 2 silk, 2 paste, outline and 2 drill files'
    run('sch','export','pdf','--output',OUT/'schematic.pdf',sch)
    run('pcb','export','svg','--mode-multi','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,F.SilkS,Edge.Cuts','--common-layers','Edge.Cuts','--exclude-drawing-sheet','--output',str(checks/'layers')+'/',board)
    (OUT/'source-sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [board,sch,ROOT/f'{STEM}.kicad_pro',ROOT/f'{STEM}.kicad_dru']},indent=2)+'\n')
    (checks/'export-log.json').write_text(json.dumps(log,indent=2)+'\n')
    print(f'Exported {len(refs)} fitted components in {len(rows)} BOM rows to {OUT}')

if __name__=='__main__':main()
