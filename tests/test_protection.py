"""Protection topology checks; electrical immunity still requires bench testing."""
import unittest
from pathlib import Path
from tools_sexp import parse, find, first

ROOT = Path(__file__).resolve().parents[1]

class ProtectionTest(unittest.TestCase):
    def test_all_protection_diodes_are_front_side_for_pcba(self):
        board = parse((ROOT / 'moisture-sensor-carrier.kicad_pcb').read_text())
        for fp in find(board, 'footprint'):
            ref = next(p[2] for p in find(fp, 'property') if p[1] == 'Reference')
            if ref in {f'D{i}' for i in range(1, 11)}:
                with self.subTest(ref=ref):
                    self.assertEqual(first(fp, 'layer')[1], 'F.Cu')
                    for pad in find(fp, 'pad'):
                        self.assertEqual(set(first(pad, 'layers')[1:]),
                                         {'F.Cu', 'F.Paste', 'F.Mask'})

    @classmethod
    def setUpClass(cls):
        board = parse((ROOT / 'moisture-sensor-carrier.kicad_pcb').read_text())
        cls.pads = {}
        for fp in find(board, 'footprint'):
            ref = next(p[2] for p in find(fp, 'property') if p[1] == 'Reference')
            cls.pads[ref] = {p[1]: first(p, 'net')[1] for p in find(fp, 'pad') if first(p, 'net')}

    def test_battery_reverse_fet_orientation_and_no_bypass(self):
        self.assertIn('Q1', self.pads, 'Battery reverse-protection FET missing')
        self.assertEqual(self.pads['Q1'], {'1': 'GND', '2': 'VBAT', '3': '/VBAT_RAW'})
        self.assertEqual(self.pads['BT1']['1'], '/VBAT_RAW')
        self.assertEqual(self.pads['U2']['3'], 'VBAT')
        for ref in ('C21', 'C22'):
            self.assertEqual(self.pads[ref]['1'], 'VBAT')

    def test_accessible_connections_have_ground_referenced_clamps(self):
        expected = {'D1': '/VBAT_RAW', 'D2': 'VBAT', 'D3': '+3V3',
                    'D4': '/SWDIO_EXT', 'D5': '/SWDCLK_EXT',
                    'D6': '/SWO_EXT', 'D7': '/RESET_EXT',
                    'D8': '/SENSE1', 'D9': '/SENSE2', 'D10': '/SHLD'}
        for ref, net in expected.items():
            with self.subTest(ref=ref):
                self.assertIn(ref, self.pads, 'ESD clamp missing')
                self.assertEqual(set(self.pads[ref].values()), {net, 'GND'})

    def test_probe_and_debug_series_resistors_separate_external_nets(self):
        for ref, ends in {'R30': ('/SENSE1', '/CIN1_PROTECTED'),
                          'R31': ('/SENSE2', '/CIN2_PROTECTED'),
                          'R32': ('/SWDIO_EXT', '/SWDIO'),
                          'R33': ('/SWDCLK_EXT', '/SWDCLK'),
                          'R34': ('/SWO_EXT', '/P2.07_SWO'),
                          'R35': ('/RESET_EXT', '/SWD_RST')}.items():
            with self.subTest(ref=ref):
                self.assertIn(ref, self.pads, 'Series isolation missing')
                self.assertEqual(set(self.pads[ref].values()), set(ends))
        self.assertEqual(self.pads['U3']['2'], '/CIN1_PROTECTED')
        self.assertEqual(self.pads['U3']['3'], '/CIN2_PROTECTED')

if __name__ == '__main__':
    unittest.main()
