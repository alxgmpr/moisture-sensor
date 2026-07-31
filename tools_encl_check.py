#!/usr/bin/env python3
"""
Hammond 1551WK corner-relief check.

Measured from lib/enclosure/1551WK_Bottom.stp and 1551WKBK.stp with cadquery
(both agree exactly). The cavity is NOT a rounded rectangle: it has four corner
bosses that run the full cavity height, and the PCB has to be scalloped to clear
them. Hammond's "Maximum PCB 74.50 x 34.50" assumes those reliefs are present.

Measured, at the height the board actually sits (Y = 6.25 mm, on the 4.00 mm
posts):

    cavity              75.090 x 35.090 mm   (walls at X +-37.545, Z +-17.545)
    corner boss radius  4.4193 mm            (4.7136 at the floor, 4.2666 at the
                                              top - draft; the board's bottom
                                              face is the worst case)
    boss centres        (+-35.75, +-15.75)   from the box centre
    posts               (+-27.50, +-12.50)   = a 55.00 x 25.00 pattern, 4.00 mm
                                               tall (Y 2.20 -> 6.20)

Reproduce with:
    uv venv .venv-cq && VIRTUAL_ENV=.venv-cq uv pip install cadquery
    .venv-cq/bin/python tools_encl_check.py
"""

import math

# Enclosure, measured from Hammond's 1551WK_Bottom.stp:
#   corner bosses R 4.4193 at the board's bottom face (Y=6.25), centres (+-35.75, +-15.75)
#   worst case over the board thickness is the bottom face (radius shrinks upward)
BOSS_R  = 4.4193
BOSS_C  = (35.75, 15.75)

# Board in-enclosure section, LAYOUT.md section 9:
#   34.0 (board x) x 74.0 (board y), R4.5 corners, four holes on 25.0 x 55.0
L, W, R = 74.0, 34.0, 4.5            # enclosure X = board y, enclosure Z = board x
hx, hz = L/2 - R, W/2 - R            # board corner arc centres, enclosure coords

print("Board corner arc centre (enclosure coords): (%.2f, %.2f), R %.2f" % (hx, hz, R))
print("Boss centre                              : (%.2f, %.2f), R %.4f" % (*BOSS_C, BOSS_R))
d = math.hypot(BOSS_C[0]-hx, BOSS_C[1]-hz)
print("Centre-to-centre distance                : %.4f mm" % d)
print()

# closest approach of the BOARD BOUNDARY to the boss centre, around the corner arc
worst = None
for k in range(0, 901):
    a = math.radians(k/10)
    x = hx + R*math.cos(a); z = hz + R*math.sin(a)
    dist = math.hypot(x-BOSS_C[0], z-BOSS_C[1])
    if worst is None or dist < worst[0]:
        worst = (dist, x, z, k/10)
print("Nearest point of the board's R4.5 corner arc to the boss centre:")
print("   (%.3f, %.3f) at %.1f deg, distance %.4f mm" % (worst[1], worst[2], worst[3], worst[0]))
print("   boss radius %.4f  ->  penetration %.3f mm  %s"
      % (BOSS_R, BOSS_R - worst[0], "INTERFERENCE" if worst[0] < BOSS_R else "clear"))
print()

# how much of the board outline sits inside the boss?
inside = 0; total = 0
for k in range(0, 901):
    a = math.radians(k/10)
    x = hx + R*math.cos(a); z = hz + R*math.sin(a)
    total += 1
    if math.hypot(x-BOSS_C[0], z-BOSS_C[1]) < BOSS_R: inside += 1
print("corner-arc samples inside the boss: %d / %d" % (inside, total))
print()

# required relief: board must stay outside a circle of BOSS_R + margin
for margin in (0.20, 0.25, 0.30):
    Rr = BOSS_R + margin
    # where that circle crosses the board's straight edges
    # edge z = W/2 (enclosure Z = 17.0):
    dz = W/2 - BOSS_C[1]
    x_cross = BOSS_C[0] - math.sqrt(max(Rr**2 - dz**2, 0))
    # edge x = L/2 (enclosure X = 37.0):
    dx = L/2 - BOSS_C[0]
    z_cross = BOSS_C[1] - math.sqrt(max(Rr**2 - dx**2, 0))
    print("margin %.2f mm -> relief arc R %.3f centred on the boss; meets board edges at" % (margin, Rr))
    print("      long edge  (board y) at enclosure X = %.3f  -> %.3f mm in from the board end" % (x_cross, L/2 - x_cross))
    print("      short edge (board x) at enclosure Z = %.3f  -> %.3f mm in from the board side" % (z_cross, W/2 - z_cross))
