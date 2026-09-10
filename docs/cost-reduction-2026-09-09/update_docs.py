"""Update current design documentation; historical audit artifacts stay intact."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[2]
for name in ['README.md', 'firmware/carrier-bringup/README.md']:
    p = ROOT / name
    p.write_text(p.read_text().replace('SHT45', 'SHT40'))

p = ROOT / 'HARDWARE.md'
s = p.read_text().replace('SHT45', 'SHT40')
s = s.replace('Mandatory 10 µF, 16 V X6S, standard 0603',
              '10 µF nominal, 25 V X5R, standard 0603 (C96446)')
s = s.replace('SHT4x datasheet v7.1.', 'SHT4x datasheet v7.3; cost revision approved 2026-09-09.')
s = s.replace('**SHT40-AD1F** — ±1.0 %RH, **±0.1 °C**, PTFE membrane',
              '**SHT40-AD1F** — typical ±1.8 %RH, **±0.2 °C**, integrated filter membrane')
a = s.index('**Why temperature accuracy is the spec that matters.**')
b = s.index('**It must sit on the always-on', a)
s = s[:a] + '''**Reference accuracy and compensation.** SHT40 is accepted as an ambient
temperature/humidity reference. It has the same 0x44 address, pin assignment,
measurement commands and conversion formulae as SHT45. The existing bring-up
firmware needs no protocol change. Typical ±0.2 °C and ±1.8 %RH values apply
under the datasheet's stated conditions; they are not full-range guarantees.

If ambient temperature is used for soil compensation, the earlier illustrative
20–60 fF/°C soil coefficient implies 4–12 fF uncertainty from ±0.2 °C, versus
2–6 fF for SHT45. That is a design estimate, not measured moisture accuracy.
Ambient temperature can differ from soil temperature; calibrate the assembled
probe over its actual conditions before using this compensation model.

The AD1F integrated membrane is retained. Sensirion's v7.3 datasheet describes
it as polyimide; older product pages describe PTFE. Procurement is locked to
the exact Sensirion SHT40-AD1F-R2 code, not an unfiltered AD1B or another brand.

''' + s[b:]
s += '''
## Cost revision — 2026-09-09

Q1 uses DMG2305UX-13 / C144153, the same Diodes device with a different reel
size. C3 uses CL10A106MA8NRNC / C96446 in the existing 0603 footprint.
Samsung's typical DC-bias data gives 6.60 µF at 3.3 V versus 6.85 µF for the
previous C3. X5R is rated −55 to +85 °C, consistent with the other retained
X5R capacitors; this is not a board temperature qualification. Total nominal
VOUT capacitance remains 12.3 µF. Existing module ripple, transient and total
effective output-capacitance qualification remains required.

C26 retains GRM155Z71A105KE01D. The screened Basic 1 µF alternative loses
about 42% at 3.3 V and has not been qualified against the FDC rail requirements.
R22/R23/R36/R37 now share the value `4.7k 1%` and C25900 so the BOM groups
all four without changing their two separate supply nets.
See [part evidence and checks](docs/cost-reduction-2026-09-09/README.md).
'''
p.write_text(s)

for name in ['LAYOUT.md', 'NEXT-STEPS.md', 'BOARD-FINISH-TODO.md']:
    p = ROOT / name
    s = p.read_text()
    note = '> 2026-09-09 cost revision: U4 is now Sensirion SHT40-AD1F-R2. The existing SHT4x footprint, membrane handling, geometry, and legacy SHT45-named model/rule areas are retained. See [cost revision](docs/cost-reduction-2026-09-09/README.md).\n\n'
    p.write_text(note + s)

p = ROOT / 'BOM.md'
s = p.read_text()
s = s.replace('docs/footprint-standardization-2026-09-09/product-bom.csv',
              'production/jlc-cost-reduced/Product-BOM.csv')
rows = list(csv.DictReader((ROOT / 'production/jlc-cost-reduced/Product-BOM.csv').open()))
a = s.index('| Ref |')
b = s.index('\n\n', a)
fields = ['Ref', 'Value', 'Footprint', 'MPN', 'Manufacturer', 'LCSC', 'JLC DNP']
table = ['| ' + ' | '.join(fields) + ' |', '| ' + ' | '.join(['---'] * len(fields)) + ' |']
table += ['| ' + ' | '.join(r[f] for f in fields) + ' |' for r in rows]
s = s[:a] + '\n'.join(table) + s[b:]
s = s.replace('SHT45 membrane', 'SHT40-AD1F membrane')
s += '\nCost revision: Q1 reel suffix, membrane-equipped SHT40, and Basic C3 are implemented; C26 is retained after DC-bias screening. [Evidence](docs/cost-reduction-2026-09-09/README.md).\n'
p.write_text(s)
