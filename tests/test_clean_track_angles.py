import math
import re
import unittest

from tools_clean_track_angles import clean_track_angles


SEGMENT = """\t(segment
\t\t(start 10 20)
\t\t(end 14 21)
\t\t(width 0.2)
\t\t(layer \"F.Cu\")
\t\t(net /TEST)
\t\t(uuid \"00000000-0000-0000-0000-000000000001\")
\t)"""


class CleanTrackAnglesTests(unittest.TestCase):
    def test_splits_off_angle_segment_into_axial_and_diagonal_legs(self):
        result, changed = clean_track_angles(SEGMENT, strategy="straight")
        self.assertEqual(changed, 1)
        points = re.findall(
            r"\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)",
            result,
        )
        self.assertEqual(len(points), 2)
        for values in points:
            x1, y1, x2, y2 = map(float, values)
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 45
            self.assertLess(min(angle, 45 - angle), 0.001)
        self.assertEqual(result.count("(net /TEST)"), 2)

    def test_leaves_already_clean_segment_unchanged(self):
        clean = SEGMENT.replace("(end 14 21)", "(end 14 24)")
        result, changed = clean_track_angles(clean)
        self.assertEqual(changed, 0)
        self.assertEqual(result, clean)


if __name__ == "__main__":
    unittest.main()
