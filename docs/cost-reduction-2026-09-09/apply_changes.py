"""Apply reviewed field-only substitutions, preserving all geometry and wiring."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools_export_bl54l15 import blocks
from tools_sexp import parse, find

CHANGES = {
    'Q1': {'Value': 'DMG2305UX-13', 'MPN': 'DMG2305UX-13', 'LCSC': 'C144153'},
    'U4': {'Value': 'SHT40-AD1F', 'MPN': 'SHT40-AD1F-R2', 'LCSC': 'C7461846'},
    'C3': {'Value': '10uF/25V X5R', 'MPN': 'CL10A106MA8NRNC', 'LCSC': 'C96446'},
    **{ref: {'Value': '4.7k 1%'} for ref in ('R22', 'R23', 'R36', 'R37')},
}

for suffix, kind in [('kicad_sch', 'symbol'), ('kicad_pcb', 'footprint')]:
    path = ROOT / f'nrf-moisture-sensor.{suffix}'
    source = path.read_text()
    changed = set()
    for a, z, block in reversed(list(blocks(source))):
        if not block.startswith('(' + kind):
            continue
        props = {p[1]: p[2] for p in find(parse(block), 'property')}
        ref = props.get('Reference')
        if ref not in CHANGES:
            continue
        for key, value in CHANGES[ref].items():
            pattern = r'(\(property "' + re.escape(key) + r'" )"(?:[^"\\]|\\.)*"'
            block, count = re.subn(pattern, lambda m: m[1] + json.dumps(value), block)
            assert count == 1, (ref, key, count)
        changed.add(ref)
        source = source[:a] + block + source[z:]
    assert changed == set(CHANGES)
    if suffix == 'kicad_sch':
        source = source.replace('FDC1004 + SHT45 |', 'FDC1004 + SHT40 |')
        source = source.replace('SHT45: main +3V3 supply.', 'SHT40: main +3V3 supply.')
    path.write_text(source)
