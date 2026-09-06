#!/usr/bin/env python3
"""Fail if any track segment is off a 45 degree multiple.

The board's routing policy is 0/45/90/135 on every layer. This is a
permanent check -- run it before fab, and after any routing session.

    python3 tools_lint_angles.py [board.kicad_pcb]

Exit 0 when clean, 1 when any segment is off-angle.
"""
import math
import re
import sys
from collections import Counter

TOL_DEG = 0.1          # snap tolerance; anything beyond this is a violation
ALLOWED = (0, 45, 90, 135, 180)

SEGMENT = re.compile(
    r'\(segment\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)'
    r'\s+\(width ([-\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net "?([^)"]*)"?\)',
    re.S,
)


def check(path):
    src = open(path).read()
    buckets = Counter()
    bad = []
    total = 0
    for m in SEGMENT.finditer(src):
        x1, y1, x2, y2 = (float(m.group(i)) for i in (1, 2, 3, 4))
        layer, net = m.group(6), m.group(7)
        total += 1
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
        nearest = min(ALLOWED, key=lambda t: abs(ang - t))
        if abs(ang - nearest) > TOL_DEG:
            bad.append((ang, math.hypot(x2 - x1, y2 - y1), layer, net, x1, y1, x2, y2))
            buckets['off'] += 1
        else:
            buckets[nearest] += 1

    print("%s: %d segments" % (path, total))
    print("  by angle: " + ", ".join(
        "%s=%d" % (k, v) for k, v in sorted(buckets.items(), key=lambda kv: str(kv[0]))))
    if not bad:
        print("  OK - every segment is on a 45 degree multiple")
        return 0

    print("  %d off-angle segments:" % len(bad))
    by_net = Counter(b[3] for b in bad)
    by_layer = Counter(b[2] for b in bad)
    print("    by layer: " + ", ".join("%s=%d" % kv for kv in by_layer.most_common()))
    print("    by net:   " + ", ".join("%s=%d" % kv for kv in by_net.most_common()))
    print("    longest first:")
    for ang, ln, layer, net, x1, y1, x2, y2 in sorted(bad, key=lambda b: -b[1]):
        print("      %7.2f deg  %5.2f mm  %-6s %-14s (%.3f,%.3f)->(%.3f,%.3f)"
              % (ang, ln, layer, net, x1, y1, x2, y2))
    return 1


if __name__ == '__main__':
    board = sys.argv[1] if len(sys.argv) > 1 else 'nrf-moisture-sensor.kicad_pcb'
    sys.exit(check(board))
