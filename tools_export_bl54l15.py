#!/usr/bin/env python3
"""Export review-only BL54L15 manufacturing files through KiCad CLI.

Does not alter the maintained schematic/board or run retired generators.
Run DRC with zone refill/save before exporting. No ordering/upload operations.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from tools_sexp import parse, find, first

ROOT = Path(__file__).resolve().parent
STEM = 'moisture-sensor-carrier'


def blocks(source):
    depth = 0
    for match in re.finditer(r'"(?:[^"\\]|\\.)*"|[()]', source):
        if match[0] == '(':
            if depth == 1:
                start = match.start()
            depth += 1
        elif match[0] == ')':
            depth -= 1
            if depth == 1:
                yield start, match.end(), source[start:match.end()]


def paste_board(source, module_only):
    """Create a derived board for one paste stage, retaining original origins."""
    for start, end, block in reversed(list(blocks(source))):
        if not block.startswith('(footprint'):
            continue
        properties = {p[1]: p[2] for p in find(parse(block), 'property')}
        is_module = properties.get('Reference') == 'U1'
        if is_module != module_only:
            source = source[:start] + source[end:]
        elif module_only:
            # This stage fits U1; remove only the instance DNP flag.
            block = re.sub(r'(\(attr[^)]*)\bdnp\b', r'\1', block)
            source = source[:start] + block + source[end:]
    return source


def product_rows(raw_rows):
    parts = json.loads((ROOT / 'docs/bl54l15/parts.json').read_text())
    return [{**row, **parts.get(row['Refs'], {}),
             'DigiKey': parts.get(row['Refs'], {}).get('DigiKey', '')}
            for row in raw_rows]


def write_csv(path, rows, fields):
    with path.open('w', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'production/bl54l15-routing-review')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli')
    if not cli:
        cli = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    board = ROOT / f'{STEM}.kicad_pcb'
    schematic = ROOT / f'{STEM}.kicad_sch'
    log = []

    def run(*command):
        result = subprocess.run([cli, *map(str, command)], check=True,
                                capture_output=True, text=True, cwd=ROOT)
        log.append({'args': list(map(str, command)), 'output': result.stdout})

    gerbers = output / 'fabrication-review'
    gerbers.mkdir(exist_ok=True)
    run('pcb', 'export', 'gerbers', '--layers',
        'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts',
        '--subtract-soldermask', '--output', str(gerbers) + '/', board)
    run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th',
        '--generate-map', '--map-format', 'svg', '--output', str(gerbers) + '/', board)
    # Default no-grouping BOM preserves individual references for metadata joins.
    for name, flags in [('product', []), ('jlc', ['--exclude-dnp'])]:
        path = output / f'{name}-bom-kicad.csv'
        run('sch', 'export', 'bom', '--output', path, *flags, schematic)
        with path.open(newline='') as file:
            rows = product_rows(list(csv.DictReader(file)))
        fields = ['Refs','Value','Footprint','Qty','DNP','Manufacturer','MPN',
                  'LCSC','DigiKey','Assembly note']
        write_csv(output / f'{name}-bom.csv', rows, fields)
        if name == 'jlc':
            assert not any(row['Refs'] == 'U1' for row in rows)
            write_csv(output / 'jlc-upload-bom-REVIEW.csv',
                      [{'Comment':r['Value'], 'Designator':r['Refs'],
                        'Footprint':r['Footprint'], 'LCSC Part #':r.get('LCSC','')}
                       for r in rows],
                      ['Comment','Designator','Footprint','LCSC Part #'])
        else:
            module = next(row for row in rows if row['Refs'] == 'U1')
            assert module['MPN'] == '453-00001R'
            assert module['DigiKey'] == '776-453-00001RCT-ND'
    position = output / 'jlc-positions-kicad.csv'
    run('pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side',
        'both', '--exclude-dnp', '--output', position, board)
    with position.open(newline='') as file:
        positions = list(csv.DictReader(file))
    assert all(p['Ref'] != 'U1' for p in positions)
    write_csv(output / 'jlc-positions-REVIEW.csv',
              [{'Designator':p['Ref'], 'Mid X':p['PosX'], 'Mid Y':p['PosY'],
                'Layer':'Top' if p['Side']=='top' else 'Bottom', 'Rotation':p['Rot']}
               for p in positions], ['Designator','Mid X','Mid Y','Layer','Rotation'])
    for name, module_only in [('jlc-paste', False), ('module-hand-fit-paste', True)]:
        stage = output / name
        stage.mkdir(exist_ok=True)
        derived = stage / f'{name}.kicad_pcb'
        derived.write_text(paste_board(board.read_text(), module_only))
        run('pcb', 'export', 'gerbers', '--layers', 'F.Paste,B.Paste',
            '--output', str(stage) + '/', derived)
    run('sch', 'export', 'pdf', '--output', output / 'schematic-review.pdf', schematic)
    run('pcb', 'export', 'svg', '--mode-multi', '--layers',
        'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,F.Silkscreen,Edge.Cuts',
        '--common-layers', 'Edge.Cuts', '--exclude-drawing-sheet',
        '--output', str(output / 'layer-review') + '/', board)
    (output / 'README-NOT-FOR-FABRICATION.md').write_text('''# Routing review only

NOT FOR FABRICATION OR ASSEMBLY ORDER. The board intentionally has unrouted
connections. Read docs/bl54l15/verification.md and finish routing, resolve BOM
candidates and qualify RF/power/assembly before issuing a release.

U1 is required in product-bom.csv and separately sourced from DigiKey. It is
excluded from JLC BOM, position and paste. The complete fabrication copper/mask
retains its pads. jlc-paste and module-hand-fit-paste are separate stencil
stages, generated from derived board copies. Do not merge their paste files.
The module stencil uses the exact 39-land apertures and original PCB origin;
use the placement drawing to align a local stencil. Thickness >=0.1 mm per Ezurio.
No paste is included in fabrication-review. Derived boards are export-only.

JLC positions use KiCad's absolute coordinate convention (X positive, Y
negative from page origin), mm, common to the source Gerbers. Confirm component
rotations and origin in the assembler preview, especially U2, U4, X1 and BT1.
C23 is a candidate; C26/C27/C28 codes and exact BT1 sourcing remain unresolved.
The upload CSVs are review aids, not approved purchasing data. No order was made.
''')
    (output / 'export-log.json').write_text(json.dumps(log, indent=2) + '\n')
    source_files = [board, schematic, ROOT/f'{STEM}.kicad_pro',
                    ROOT/f'{STEM}.kicad_dru', ROOT/'docs/bl54l15/parts.json',
                    ROOT/'lib/ezurio.kicad_sym',
                    ROOT/'lib/footprints.pretty/Ezurio_BL54L15_453-00001.kicad_mod']
    manifest = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in source_files}
    (output / 'source-sha256.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Exported REVIEW ONLY package: {output}')


if __name__ == '__main__':
    main()
