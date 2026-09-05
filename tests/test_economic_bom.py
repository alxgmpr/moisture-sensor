import unittest
from pathlib import Path
from tools_sexp import parse, find, first
ROOT = Path(__file__).resolve().parents[1]
class EconomicBomTests(unittest.TestCase):
    def test_explicit_economic_selections_match_board(self):
        sch = parse((ROOT/'moisture-sensor-carrier.kicad_sch').read_text())
        pcb = parse((ROOT/'moisture-sensor-carrier.kicad_pcb').read_text())
        syms = {dict((p[1],p[2]) for p in find(s,'property')).get('Reference'):s for s in find(sch,'symbol')}
        fps = {dict((p[1],p[2]) for p in find(f,'property')).get('Reference'):f for f in find(pcb,'footprint')}
        expected = {'C22':'C1523','C24':'C1523','C27':'C1525','C28':'C1525','C26':'C528974','R30':'C25905','R31':'C25905','BT1':'C22363833'}
        for ref,code in expected.items():
            props = {p[1]:p[2] for p in find(syms[ref],'property')}
            self.assertEqual(props.get('LCSC'),code,ref)
            self.assertEqual(props['Footprint'],fps[ref][1],ref)
        for ref in ['C22','C24','C27','C28']:
            self.assertEqual(fps[ref][1],'Capacitor_SMD:C_0402_1005Metric')
        for ref in ['U1']:
            self.assertEqual(first(syms[ref],'dnp'),['dnp','yes'])
            self.assertIn('dnp',first(fps[ref],'attr'))

        self.assertEqual(first(syms['BT1'],'dnp'),['dnp','no'])
        self.assertNotIn('dnp',first(fps['BT1'],'attr'))
        pads={p[1]:p for p in find(fps['BT1'],'pad')}
        self.assertAlmostEqual(float(first(pads['2'],'at')[1])-float(first(pads['1'],'at')[1]),30.6)
        for pad in pads.values():
            self.assertEqual(list(map(float,first(pad,'size')[1:])),[1.9,5.0])
