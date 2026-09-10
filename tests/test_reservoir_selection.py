"""Both PMIC reservoirs must use a capacitor from Nordic nwp_058 tables 6/8.
This enforces the reviewed selection, not a guarantee for capacitor production lots.
"""
import unittest
from pathlib import Path
from tools_sexp import parse,find
ROOT=Path(__file__).resolve().parents[1]
class ReservoirSelection(unittest.TestCase):
    def test_exact_nordic_reference_reservoirs(self):
        approved={'GRM158R60J226ME01D','CL05A106MQ5NUW','GRM155R60J106ME05','GRM155R60J106ME15'}
        for suffix,kind in [('kicad_sch','symbol'),('kicad_pcb','footprint')]:
            b=parse((ROOT/f'nrf-moisture-sensor.{suffix}').read_text())
            for n in find(b,kind):
                p={p[1]:p[2] for p in find(n,'property')}
                if p.get('Reference') in ['C21','C23']:
                    with self.subTest(source=suffix,ref=p['Reference']):self.assertIn(p.get('MPN'),approved)
