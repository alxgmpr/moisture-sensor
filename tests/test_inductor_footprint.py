"""Placed inductor pads must follow the terminal orientation of its footprint."""
import unittest
from pathlib import Path

from tools_sexp import parse, find, first

ROOT = Path(__file__).resolve().parents[1]


class InductorFootprintTest(unittest.TestCase):
    def test_l10_pad_rectangles_follow_footprint_rotation(self):
        board = parse((ROOT / 'moisture-sensor-carrier.kicad_pcb').read_text())
        fp = next(f for f in find(board, 'footprint')
                  if any(p[1:3] == ['Reference', 'L10'] for p in find(f, 'property')))
        rotation = float(first(first(fp, 'transform'), 'rotate')[1])
        for pad in find(fp, 'pad'):
            at = first(pad, 'at')
            angle = float(at[3]) if len(at) > 3 else 0
            with self.subTest(pad=pad[1]):
                self.assertAlmostEqual((angle - rotation) % 180, 0)
                self.assertEqual(list(map(float, first(pad, 'size')[1:])), [0.55, 1.2])


if __name__ == '__main__':
    unittest.main()
