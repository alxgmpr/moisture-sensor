import math
import unittest

from tools_finish_routes import ROUTES, add_finish_routes


class FinishRoutesTests(unittest.TestCase):
    def test_all_route_legs_are_axial_or_45_degrees(self):
        for name, net, layer, width, points in ROUTES:
            for start, end in zip(points, points[1:]):
                with self.subTest(route=name, start=start, end=end):
                    angle = math.degrees(
                        math.atan2(end[1] - start[1], end[0] - start[0])
                    ) % 45
                    self.assertLess(min(angle, 45 - angle), 0.001)

    def test_insertion_is_idempotent(self):
        board = "(kicad_pcb\n)\n"
        once = add_finish_routes(board)
        twice = add_finish_routes(once)
        self.assertEqual(once, twice)

if __name__ == "__main__":
    unittest.main()
