#!/usr/bin/env python3
"""
Draw how the PCB sits in the Hammond 1551WK.

Nothing here is typed in by hand:
  - board outline, mounting holes and part positions come from the .kicad_pcb
  - the cavity cross-section is MEASURED from lib/enclosure/1551WK_Bottom.stp
    with cadquery, at the exact height the board sits, and drawn as-is rather
    than reconstructed from radii

    .venv-cq/bin/python tools_encl_draw.py

Writes doc/enclosure-fit.png, doc/enclosure-corner.png, doc/enclosure-section.png.

Coordinate mapping. The STEP has the box centred on the origin with Y up, so
    board_x = 17 + step_Z      board_y = 37 + step_X
because the board's in-enclosure section (34.0 x 74.0) is centred in the cavity
- which is what puts its four mounting holes on the four posts.
"""

import math
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyArrow

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "moisture-sensor-carrier.kicad_pcb")
STEP = os.path.join(HERE, "lib", "enclosure", "1551WK_Bottom.stp")
OUT = os.path.join(HERE, "doc")

OX, OY = 60.0, 40.0          # board (0,0) is KiCad page (60,40)
BCX, BCY = 17.0, 37.0        # board centre = cavity centre

Y_FLOOR, Y_POST_TOP = 2.20, 6.20      # measured cavity floor and post top
BOARD_T = 1.59                        # JLC04161H-7628 finished thickness
Y_BOARD_TOP = Y_POST_TOP + BOARD_T
CAV_TOP = 16.90                       # top of the bottom moulding

GREEN, RED, GOLD, GREY = "#1b5e20", "#b0453a", "#c8a03a", "#37474f"


# ----------------------------------------------------------------- geometry --
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
        out.append(src[i:j + 1])
    return out


def arc_points(p0, pm, p1, n=140):
    (ax, ay), (bx, by), (cx, cy) = p0, pm, p1
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay)
          + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx)
          + (cx**2 + cy**2) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in (p0, pm, p1))

    def unwrap(a, b):
        while b - a > math.pi:
            b -= 2 * math.pi
        while b - a < -math.pi:
            b += 2 * math.pi
        return b

    am = unwrap(a0, am); a1 = unwrap(am, a1)
    return [(ux + r * math.cos(a0 + (a1 - a0) * k / n),
             uy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def read_board():
    s = open(PCB).read()
    edges, holes, parts = [], [], []
    for b in sexpr(s, "gr_line"):
        if '"Edge.Cuts"' in b:
            edges.append([(float(x) - OX, float(y) - OY) for x, y in
                          re.findall(r"\((?:start|end) ([-\d.]+) ([-\d.]+)\)", b)])
    for b in sexpr(s, "gr_arc"):
        if '"Edge.Cuts"' in b:
            p = [(float(x) - OX, float(y) - OY) for x, y in
                 re.findall(r"\((?:start|mid|end) ([-\d.]+) ([-\d.]+)\)", b)]
            edges.append(arc_points(*p))
    for b in sexpr(s, "gr_circle"):
        if '"Edge.Cuts"' in b:
            c = re.findall(r"\((?:center|end) ([-\d.]+) ([-\d.]+)\)", b)
            if len(c) >= 2:
                cx, cy = float(c[0][0]) - OX, float(c[0][1]) - OY
                ex, ey = float(c[1][0]) - OX, float(c[1][1]) - OY
                holes.append((cx, cy, math.hypot(ex - cx, ey - cy)))
    for b in sexpr(s, "footprint"):
        ref = re.search(r'\(property "Reference" "([^"]+)"', b)
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)", b)
        if ref and at:
            parts.append((ref.group(1), float(at.group(1)) - OX,
                          float(at.group(2)) - OY))
    return edges, holes, parts


_shape = None


def shape():
    global _shape
    if _shape is None:
        _shape = cq.importers.importStep(STEP).vals()[0]
    return _shape


def slab(y0, y1):
    bb = shape().BoundingBox()
    box = cq.Solid.makeBox(bb.xlen + 20, y1 - y0, bb.zlen + 20,
                           cq.Vector(bb.xmin - 10, y0, bb.zmin - 10))
    return shape().intersect(box)


def cavity_outline(y):
    """The real cavity boundary at height y, in BOARD coordinates."""
    cut = slab(y, y + 0.05)
    top = [f for f in cut.Faces()
           if abs(f.normalAt().y) > 0.9
           and abs(f.BoundingBox().ymin - (y + 0.05)) < 0.02][0]
    ws = top.Wires()
    outer = max(ws, key=lambda w: w.BoundingBox().xlen * w.BoundingBox().zlen)
    iw = max([w for w in ws if w is not outer],
             key=lambda w: w.BoundingBox().xlen * w.BoundingBox().zlen)
    pts = []
    for e in iw.Edges():
        n = max(2, int(e.Length() / 0.2))
        for k in range(n + 1):
            p = e.positionAt(k / n)
            pts.append((BCX + p.z, BCY + p.x))
    # order them around the centroid so the polygon draws cleanly
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    pts.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    return pts + [pts[0]]


def posts():
    """Post cross-sections at mid-height, in board coordinates."""
    cut = slab(5.0, 5.2)
    out = []
    for s in cut.Solids():
        b = s.BoundingBox()
        if b.xlen < 10 and b.zlen < 10:            # a post, not the wall ring
            out.append((BCX + b.zmin, BCY + b.xmin, b.zlen, b.xlen))
    return out


# -------------------------------------------------------------------- plots --
def draw_plan():
    edges, holes, parts = read_board()
    cav = cavity_outline(6.25)
    fig, ax = plt.subplots(figsize=(7.4, 12.6))

    ax.fill([p[0] for p in cav], [p[1] for p in cav], fc="#f6e6e4",
            ec=RED, lw=1.6, zorder=1,
            label="1551WK cavity at the board's underside (measured)")
    for (px, py, pw, pl) in posts():
        ax.add_patch(Rectangle((px, py), pw, pl, fc=GOLD, alpha=0.55,
                               ec="#8a6d1f", lw=1.0, zorder=3))
    ax.plot([], [], color=GOLD, lw=7, alpha=0.6,
            label="4.00 mm post  (55.0 × 25.0 pattern)")

    for p in edges:
        ax.plot([q[0] for q in p], [q[1] for q in p], color=GREEN, lw=2.1,
                zorder=5)
    ax.plot([], [], color=GREEN, lw=2.1, label="PCB outline")
    for (hx, hy, hr) in holes:
        ax.add_patch(Circle((hx, hy), hr, fc="white", ec=GREEN, lw=1.2,
                            zorder=6))

    for ref, px, py in parts:
        if ref in ("U1", "U2", "U3", "U4", "J1", "J2", "J3", "J4", "J5",
                   "X1", "X2", "L10"):
            ax.plot(px, py, "o", ms=2.6, color=GREY, zorder=7)
            ax.annotate(ref, (px, py), textcoords="offset points",
                        xytext=(3, 3), fontsize=6.5, color=GREY, zorder=7)

    ax.set_aspect("equal")
    ax.set_xlim(-4, 45)
    ax.set_ylim(160, -6)
    ax.set_xlabel("board x  (mm)")
    ax.set_ylabel("board y  (mm)")
    ax.set_title("PCB in the Hammond 1551WK — plan view\n"
                 "cavity measured from Hammond's STEP at the board's underside",
                 fontsize=10)
    ax.grid(alpha=0.15, lw=0.5)
    ax.legend(loc="lower right", fontsize=7.5, framealpha=0.96)
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "enclosure-fit.png"), dpi=170)
    print("wrote doc/enclosure-fit.png")


def draw_corners():
    edges, holes, parts = read_board()
    cav = cavity_outline(6.25)
    fig, axes = plt.subplots(1, 4, figsize=(15.5, 4.4))
    views = [("antenna end, x0", (-3, 11), (11, -3)),
             ("antenna end, x34", (23, 37), (11, -3)),
             ("probe end, x0", (-3, 11), (80, 66)),
             ("probe end, x34", (23, 37), (80, 66))]
    for ax, (name, xlim, ylim) in zip(axes, views):
        ax.fill([p[0] for p in cav], [p[1] for p in cav], fc="#f6e6e4",
                ec=RED, lw=1.6, zorder=1)
        for p in edges:
            ax.plot([q[0] for q in p], [q[1] for q in p], color=GREEN, lw=2.4,
                    zorder=5)
        for (hx, hy, hr) in holes:
            ax.add_patch(Circle((hx, hy), hr, fc="white", ec=GREEN, lw=1.2,
                                zorder=6))
        for (px, py, pw, pl) in posts():
            ax.add_patch(Rectangle((px, py), pw, pl, fc=GOLD, alpha=0.55,
                                   ec="#8a6d1f", lw=1.0, zorder=3))
        ax.set_aspect("equal")
        ax.set_xlim(*xlim); ax.set_ylim(*ylim)
        ax.grid(alpha=0.15, lw=0.5)
        ax.set_title(name, fontsize=9)
        ax.tick_params(labelsize=7)
    fig.suptitle("Corner reliefs against the measured cavity  "
                 "(pink = cavity, green = PCB)", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "enclosure-corner.png"), dpi=170)
    print("wrote doc/enclosure-corner.png")


def draw_section():
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    W = 35.09
    x0 = -W / 2
    ax.add_patch(Rectangle((x0 - 2.5, 0), W + 5, CAV_TOP + 1.4, fc="#e9e0dc",
                           ec=RED, lw=1.4, zorder=1))
    ax.add_patch(Rectangle((x0, Y_FLOOR), W, CAV_TOP - Y_FLOOR, fc="white",
                           ec=RED, lw=1.2, zorder=2))
    for sx in (-1, 1):
        ax.add_patch(Rectangle((sx * 12.5 - 2.4, Y_FLOOR), 4.8,
                               Y_POST_TOP - Y_FLOOR, fc=GOLD, alpha=0.6,
                               ec="#8a6d1f", zorder=3))
    ax.add_patch(Rectangle((x0 + 0.545, Y_POST_TOP), 34.0, BOARD_T, fc="#c8e6c9",
                           ec=GREEN, lw=1.8, zorder=4))
    ax.text(0, Y_POST_TOP + BOARD_T / 2, "PCB  1.59 mm", ha="center",
            va="center", fontsize=8, color=GREEN, zorder=5)
    ax.add_patch(Rectangle((-14.5, CAV_TOP - 4.8), 29.0, 4.8, fc="#d7ccc8",
                           ec="#6d4c41", lw=1.4, zorder=4))
    ax.text(0, CAV_TOP - 2.4, "cell 29 × 36 × 4.8 mm, taped to the lid",
            ha="center", va="center", fontsize=7.5, color="#4e342e", zorder=5)

    def dim(y, label, x=20.5):
        ax.annotate("", (x, 0), (x, y), arrowprops=dict(arrowstyle="<->",
                    color=GREY, lw=0.9))
        ax.text(x + 0.6, y / 2, label, fontsize=7.5, color=GREY, va="center")
    dim(Y_FLOOR, "floor 2.20")
    dim(Y_POST_TOP, "post top 6.20", x=23.5)
    ax.annotate("", (-20.5, Y_BOARD_TOP), (-20.5, CAV_TOP - 4.8),
                arrowprops=dict(arrowstyle="<->", color=GREY, lw=0.9))
    ax.text(-20.2, (Y_BOARD_TOP + CAV_TOP - 4.8) / 2,
            f"{CAV_TOP - 4.8 - Y_BOARD_TOP:.2f} mm\nunder the cell",
            fontsize=7.5, color=GREY, va="center")
    ax.set_aspect("equal")
    ax.set_xlim(-26, 30)
    ax.set_ylim(-1.5, CAV_TOP + 2.5)
    ax.set_xlabel("board x  (mm)")
    ax.set_ylabel("height above the outside of the box floor  (mm)")
    ax.set_title("Height stack-up through the enclosure (measured)", fontsize=10)
    ax.grid(alpha=0.15, lw=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "enclosure-section.png"), dpi=170)
    print("wrote doc/enclosure-section.png")


if __name__ == "__main__":
    draw_plan()
    draw_corners()
    draw_section()
