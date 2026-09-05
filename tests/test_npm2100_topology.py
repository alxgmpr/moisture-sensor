"""Check Nordic's QFN boost topology in the schematic and PCB pad nets."""
import unittest
from pathlib import Path

from tools_netcmp import netlist
from tools_sexp import parse, find, first

ROOT = Path(__file__).resolve().parents[1]


class Npm2100TopologyTest(unittest.TestCase):
    def test_schematic_inductor_connects_sw_to_protected_vbat(self):
        nets = netlist()
        self.assertEqual(set(nets['SW']), {'U2.2', 'L10.1'})
        self.assertIn('L10.2', nets['VBAT'])
        self.assertTrue({'U2.3', 'Q1.2', 'C21.1', 'C22.1'} <= set(nets['VBAT']))
        self.assertEqual(set(nets['VINT']), {'U2.14', 'U2.15', 'C23.1', 'C24.1'})

    def test_board_inductor_pad_nets_match_reference(self):
        board = parse((ROOT / 'moisture-sensor-carrier.kicad_pcb').read_text())
        pads = {}
        for fp in find(board, 'footprint'):
            ref = next(p[2] for p in find(fp, 'property') if p[1] == 'Reference')
            pads[ref] = {p[1]: first(p, 'net')[1] for p in find(fp, 'pad') if first(p, 'net')}
        self.assertEqual(pads['L10'], {'1': '/SW', '2': 'VBAT'})
        self.assertEqual(pads['L10']['1'], pads['U2']['2'])
        self.assertEqual(pads['L10']['2'], pads['U2']['3'])
        self.assertEqual(pads['L10']['2'], pads['Q1']['2'])
        for ref, pin in [('U2', '14'), ('U2', '15'), ('C23', '1'), ('C24', '1')]:
            self.assertEqual(pads[ref][pin], '/VINT')


if __name__ == '__main__':
    unittest.main()
