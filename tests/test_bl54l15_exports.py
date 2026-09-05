"""Keep the hand-fitted LGA out of the outsourced assembly stage."""
import unittest
from pathlib import Path
from tools_sexp import parse, find, first
from tools_export_bl54l15 import paste_board, product_rows

ROOT = Path(__file__).resolve().parents[1]

class ModuleAssemblyExportTest(unittest.TestCase):
    def test_paste_stages_are_disjoint(self):
        source = (ROOT / 'moisture-sensor-carrier.kicad_pcb').read_text()
        refs = []
        for module_only in (False, True):
            board = parse(paste_board(source, module_only))
            refs.append({first(f, 'property')[2] for f in find(board, 'footprint')})
        self.assertNotIn('U1', refs[0])
        self.assertTrue({'C3', 'X1', 'U4'} <= refs[0])
        self.assertEqual(refs[1], {'U1'})
        self.assertFalse(refs[0] & refs[1])
        module = find(parse(paste_board(source, True)), 'footprint')[0]
        self.assertEqual(len(find(module, 'pad')), 39)
        self.assertNotIn('dnp', first(module, 'attr'))

    def test_product_bom_retains_separately_ordered_module(self):
        rows = product_rows([{'Refs':'U1','Value':'BL54L15','Footprint':'LGA39','Qty':'1','DNP':'DNP'}])
        self.assertEqual(rows[0]['MPN'], '453-00001R')
        self.assertEqual(rows[0]['DigiKey'], '776-453-00001RCT-ND')
        self.assertIn('HAND FIT', rows[0]['Assembly note'])
        self.assertEqual(rows[0]['DNP'], 'DNP')
