#!/usr/bin/env python3
"""Measure switching-loop geometry from pad positions.

    python3 tools_loop_area.py [board.kicad_pcb]

Reports, per loop, the conductor runs and the enclosed area.

WHY THIS IS A SCRIPT AND NOT A ONE-LINER: the shoelace formula silently lies
about a self-intersecting path. It sums SIGNED triangle areas, so a loop that
doubles back on itself cancels part of its own area and comes out smaller than
it is. The nPM2100 boost loop can do exactly that when the pad order doubles
back through the inductor and output capacitor. Worse, "fixing"
the geometry then made the reported number go UP, because the corrected path no
longer self-intersects.

So: detect self-intersection, and report the convex hull, which is
order-independent and cannot be gamed by the sequence the pads are listed in.
"""

import math
import re
import sys


def pads(path):
    """Pad centres in board coordinates, keyed "REF.PAD"."""
    src = open(path).read()
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', src)
    stack = [[]]
    for t in tok:
        if t == '(':
            stack.append([])
        elif t == ')':
            v = stack.pop()
            stack[-1].append(v)
        elif t.startswith('"'):
            stack[-1].append(t[1:-1])
        else:
            stack[-1].append(t)
    root = stack[0][0]

    def find(n, k):
        return [c for c in n if isinstance(c, list) and c and c[0] == k]

    def first(n, k):
        r = find(n, k)
        return r[0] if r else None

    # board origin = Edge.Cuts minimum
    xs, ys = [], []
    for kind in ('gr_line', 'gr_arc', 'gr_poly', 'gr_rect', 'gr_circle'):
        for g in find(root, kind):
            lay = first(g, 'layer')
            if not lay or lay[1] != 'Edge.Cuts':
                continue
            for key in ('start', 'end', 'mid', 'center'):
                for p in find(g, key):
                    xs.append(float(p[1]))
                    ys.append(float(p[2]))
    ox, oy = (min(xs), min(ys)) if xs else (0.0, 0.0)

    out = {}
    for fp in find(root, 'footprint'):
        at = first(fp, 'at')
        if at:
            fx, fy = float(at[1]), float(at[2])
            frot = math.radians(float(at[3]) if len(at) > 3 else 0.0)
        else:
            # KiCad 10 board footprints use a transform block instead of the
            # legacy top-level (at x y angle) form.
            transform = first(fp, 'transform')
            translate = first(transform, 'translate') if transform else None
            rotate = first(transform, 'rotate') if transform else None
            if not translate:
                continue
            fx, fy = float(translate[1]), float(translate[2])
            frot = math.radians(float(rotate[1]) if rotate else 0.0)
        ref = None
        for pr in find(fp, 'property'):
            if len(pr) > 2 and pr[1] == 'Reference':
                ref = pr[2]
        if ref is None:
            continue
        ca, sa = math.cos(frot), math.sin(frot)
        for pad in find(fp, 'pad'):
            pat = first(pad, 'at')
            px, py = float(pat[1]), float(pat[2])
            out[f"{ref}.{pad[1]}"] = (fx + px * ca + py * sa - ox,
                                      fy - px * sa + py * ca - oy)
    return out


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    def half(ps):
        st = []
        for p in ps:
            while len(st) >= 2 and _cross(st[-2], st[-1], p) <= 0:
                st.pop()
            st.append(p)
        return st
    return half(pts)[:-1] + half(pts[::-1])[:-1]


def area(p):
    a = 0.0
    for i in range(len(p)):
        x1, y1 = p[i]
        x2, y2 = p[(i + 1) % len(p)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def self_intersecting(p):
    def hits(a, b, c, d):
        def o(u, v, w):
            val = (v[1] - u[1]) * (w[0] - v[0]) - (v[0] - u[0]) * (w[1] - v[1])
            return 0 if abs(val) < 1e-9 else (1 if val > 0 else 2)
        return o(a, b, c) != o(a, b, d) and o(c, d, a) != o(c, d, b)
    n = len(p)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if hits(p[i], p[(i + 1) % n], p[j], p[(j + 1) % n]):
                return True
    return False


LOOPS = {
    "nPM2100 BOOST  SW -> L10 -> C23 -> PVSS":
        ["U2.2", "L10.1", "L10.2", "C23.1", "C23.2", "U2.16"],
    "nRF54L15 DCDC  DCC -> L1 -> C1 -> VSS":
        ["U1.46", "L1.1", "L1.2", "C1.1", "C1.2", "U1.44"],
}


def main():
    board = sys.argv[1] if len(sys.argv) > 1 else 'moisture-sensor-carrier.kicad_pcb'
    P = pads(board)
    rc = 0
    for name, keys in LOOPS.items():
        missing = [k for k in keys if k not in P]
        print("\n=== %s ===" % name)
        if missing:
            print("   missing pads: %s" % missing)
            rc = 1
            continue
        pts = [P[k] for k in keys]
        for k in keys:
            print("   %-8s (%7.3f, %7.3f)" % (k, P[k][0], P[k][1]))
        runs = [(keys[i], keys[i + 1], math.dist(pts[i], pts[i + 1]))
                for i in range(len(pts) - 1)]
        for a, b, d in runs:
            print("   run %-8s -> %-8s %6.2f mm" % (a, b, d))
        si = self_intersecting(pts)
        h = hull(pts)
        print("   enclosed area (hull) : %6.2f mm2" % area(h))
        if si:
            print("   NOTE: the pad path self-intersects, so the shoelace area "
                  "(%.2f) understates it. Hull figure above is the one to use."
                  % area(pts))
    return rc


if __name__ == '__main__':
    sys.exit(main())
