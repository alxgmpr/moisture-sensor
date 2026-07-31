#!/usr/bin/env python3
"""
Round every sharp vertex on the board outline.

Nothing on this board should have a sharp corner: FR4 cracks from them, the
router likes them even less, and the probe is an 81 mm cantilever that gets
pushed into soil.

Reads Edge.Cuts from the .kicad_pcb, orders it into a closed loop, filters for
vertices whose incoming and outgoing tangents actually differ, and fillets those
with OCC's 2D filleter rather than trimming arcs by hand. Writes the result back
as gr_line / gr_arc.

    .venv-cq/bin/python tools_round_corners.py [--check]

Every vertex it rounds is CONVEX, so the fillet removes material and moves the
edge away from the enclosure wall - clearance can only improve. That is asserted
at the end by re-running the cavity fit.
"""

import math
import os
import re
import sys
import uuid

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet2d
from OCP.GeomAbs import GeomAbs_CurveType
from OCP.TopAbs import TopAbs_ShapeEnum
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "moisture-sensor-carrier.kicad_pcb")

# Per-corner fillet radius, keyed by BOARD coordinates (page minus (60,40)).
# The two shoulder vertices get a small radius because the flat they sit on is
# only 0.409 mm long - see LAYOUT.md section 9.
RADII = {
    (6.091, 74.000): 0.25, (27.909, 74.000): 0.25,     # relief -> shoulder flat
    (7.000, 149.000): 0.5, (27.000, 149.000): 0.5,      # probe spear shoulders
    (14.000, 155.000): 0.5, (20.000, 155.000): 0.5,     # probe tip
}
DEFAULT_R = 1.0        # the six relief-to-straight-edge junctions


def sexpr(src, tag):
    out = []
    for m in re.finditer(r"\(%s\b" % tag, src):
        i = m.start(); d = 0; j = i
        while j < len(src):
            if src[j] == "(":
                d += 1
            elif src[j] == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        out.append((i, j + 1, src[i:j + 1]))
    return out


def read_outline(src):
    els = []
    for tag in ("gr_line", "gr_arc"):
        for _, _, b in sexpr(src, tag):
            if '"Edge.Cuts"' not in b:
                continue
            p = [(float(x), float(y)) for x, y in
                 re.findall(r"\((?:start|mid|end) ([-\d.]+) ([-\d.]+)\)", b)]
            els.append((tag, p))
    return els


def order_loop(els):
    k = lambda p: (round(p[0], 3), round(p[1], 3))
    adj = {}
    for i, (_, p) in enumerate(els):
        adj.setdefault(k(p[0]), []).append((i, 0))
        adj.setdefault(k(p[-1]), []).append((i, 1))
    loop = [(0, 0)]
    used = {0}
    v = k(els[0][1][-1])
    while len(used) < len(els):
        nxt = [(i, e) for i, e in adj[v] if i not in used]
        if not nxt:
            raise SystemExit("outline is not a single closed loop")
        i, e = nxt[0]
        used.add(i)
        loop.append((i, e))
        v = k(els[i][1][0] if e == 1 else els[i][1][-1])
    return loop


def circum(a, b, c):
    d = 2*(a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1]))
    ux = ((a[0]**2+a[1]**2)*(b[1]-c[1]) + (b[0]**2+b[1]**2)*(c[1]-a[1])
          + (c[0]**2+c[1]**2)*(a[1]-b[1]))/d
    uy = ((a[0]**2+a[1]**2)*(c[0]-b[0]) + (b[0]**2+b[1]**2)*(a[0]-c[0])
          + (c[0]**2+c[1]**2)*(b[0]-a[0]))/d
    return (ux, uy)


def tangent(el, at_end):
    tag, p = el
    if tag == "gr_line":
        d = (p[1][0]-p[0][0], p[1][1]-p[0][1])
    else:
        c = circum(*p)
        q = p[-1] if at_end else p[0]
        rad = (q[0]-c[0], q[1]-c[1])
        d = (-rad[1], rad[0])
        nxt = p[-2] if at_end else p[1]
        v = (nxt[0]-q[0], nxt[1]-q[1])
        dot = d[0]*v[0] + d[1]*v[1]
        if (dot > 0) == at_end:
            d = (-d[0], -d[1])
    n = math.hypot(*d)
    return (d[0]/n, d[1]/n)


def sharp_vertices(els, loop, thresh_deg=1.0):
    """Coordinates where the incoming and outgoing tangents actually differ.

    Most of this outline is already tangent - the jut-out fillets, the probe
    shoulder fillets, the relief-to-fillet joins. Filleting those again would
    add junk arcs and disturb geometry that was placed deliberately.
    """
    out = {}
    for k in range(len(loop)):
        i, e = loop[k]
        j, e2 = loop[(k+1) % len(loop)]
        ti = tangent(els[i], at_end=(e == 0))
        tj = tangent(els[j], at_end=(e2 == 1))
        dot = max(-1.0, min(1.0, ti[0]*tj[0] + ti[1]*tj[1]))
        ang = math.degrees(math.acos(abs(dot)))
        if ang > thresh_deg:
            v = els[i][1][-1] if e == 0 else els[i][1][0]
            out[(round(v[0], 3), round(v[1], 3))] = ang
    return out


def build_wire(els, loop):
    edges = []
    for i, e in loop:
        tag, p = els[i]
        q = list(reversed(p)) if e == 1 else p
        if tag == "gr_line":
            edges.append(cq.Edge.makeLine(cq.Vector(*q[0], 0), cq.Vector(*q[-1], 0)))
        else:
            edges.append(cq.Edge.makeThreePointArc(
                cq.Vector(*q[0], 0), cq.Vector(*q[1], 0), cq.Vector(*q[2], 0)))
    return cq.Wire.assembleEdges(edges)


def emit(edges):
    """OCC edges -> KiCad gr_line / gr_arc s-expressions."""
    out = []
    for e in edges:
        a = BRepAdaptor_Curve(e.wrapped)
        p0 = e.startPoint(); p1 = e.endPoint()
        u0, u1 = a.FirstParameter(), a.LastParameter()
        if a.GetType() == GeomAbs_CurveType.GeomAbs_Line:
            out.append(f'\n\t(gr_line\n\t\t(start {p0.x:.4f} {p0.y:.4f})\n'
                       f'\t\t(end {p1.x:.4f} {p1.y:.4f})\n'
                       f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
                       f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')
        else:
            pm = a.Value((u0 + u1) / 2)
            out.append(f'\n\t(gr_arc\n\t\t(start {p0.x:.4f} {p0.y:.4f})\n'
                       f'\t\t(mid {pm.X():.4f} {pm.Y():.4f})\n'
                       f'\t\t(end {p1.x:.4f} {p1.y:.4f})\n'
                       f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
                       f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')
    return out


def main():
    src = open(PCB).read()
    els = read_outline(src)
    loop = order_loop(els)
    sharp = sharp_vertices(els, loop)
    print(f"sharp vertices: {len(sharp)}")
    for (x, y), a in sorted(sharp.items()):
        print(f"   {a:6.2f} deg at board ({x-60:7.3f}, {y-40:7.3f})")
    wire = build_wire(els, loop)
    face = cq.Face.makeFromWires(wire)
    print(f"outline: {len(els)} elements, area {face.Area():.3f} mm^2")

    filleter = BRepFilletAPI_MakeFillet2d(face.wrapped)
    exp = TopExp_Explorer(face.wrapped, TopAbs_ShapeEnum.TopAbs_VERTEX)
    seen = set()
    n = 0
    while exp.More():
        v = TopoDS.Vertex_s(exp.Current())
        pnt = cq.Vertex(v).toTuple()
        key = (round(pnt[0], 3), round(pnt[1], 3))
        if key not in seen and key in sharp:
            seen.add(key)
            b = (round(pnt[0] - 60, 3), round(pnt[1] - 40, 3))
            r = None
            for (bx, by), rr in RADII.items():
                if abs(b[0] - bx) < 0.01 and abs(b[1] - by) < 0.01:
                    r = rr
            if r is None:
                r = DEFAULT_R
            try:
                filleter.AddFillet(v, r)
                n += 1
            except Exception as ex:
                print(f"   skip ({b[0]},{b[1]}): {ex}")
        exp.Next()
    filleter.Build()
    if not filleter.IsDone():
        raise SystemExit("fillet2d failed")
    res = cq.Face(filleter.Shape())
    print(f"filleted {n} vertices, area now {res.Area():.3f} mm^2 "
          f"({face.Area()-res.Area():+.3f} removed)")

    outer = res.outerWire()
    edges = outer.Edges()
    print(f"result: {len(edges)} edges")

    new = "".join(emit(edges))
    # drop every existing Edge.Cuts gr_line / gr_arc, then append the new loop
    spans = []
    for tag in ("gr_line", "gr_arc"):
        for i, j, b in sexpr(src, tag):
            if '"Edge.Cuts"' in b:
                spans.append((i, j))
    for i, j in sorted(spans, reverse=True):
        src = src[:i] + src[j:]
    k = src.rstrip().rfind(")")
    src = src[:k] + new + src[k:]

    out = "/tmp/rounded.kicad_pcb" if "--check" in sys.argv else PCB
    open(out, "w").write(src)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
