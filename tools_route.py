#!/usr/bin/env python3
"""
Routing for the moisture sensor carrier.

Why this exists as a script when tools_gen_pcb.py is frozen: the generator is
frozen because it redraws *graphics and placement*, and the board's jut-out
fillets are hand-drawn. This script never touches graphics, footprints or zone
outlines. It only removes and re-adds copper tracks and vias, then refills the
zones - so it is safe to re-run, and the routing stays reviewable as text
instead of as a binary diff.

    python3 tools_route.py            # route
    python3 tools_route.py --check    # route into /tmp and report, leave board alone

Coordinates are KiCad page mm. The board sits at x 60..102, y 40..195, so
board (0,0) is page (60,40).

Order follows NEXT-STEPS.md: RF first while there is freedom, then the SW2
loop, then sense into the probe, then everything else.
"""

import os
import sys

import pcbnew

BOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "moisture-sensor-carrier.kicad_pcb")

F, B, IN1, IN2 = "F.Cu", "B.Cu", "In1.Cu", "In2.Cu"


# --------------------------------------------------------------------------
# RF. See LAYOUT.md section 2 and section 3.
#
# The chain runs up a single column at x = 76.8, which is where U1 pin 31 sits
# after the package was rotated 90 degrees:
#
#     U1.31  60.079   /ANT
#     L2.1   58.82           C6.1  74.58,58.5   shunt, /RF_A
#     L2.2   58.18   /RF_A   C6.2  75.22,58.5   -> U1.32, top layer only
#     L3.1   57.22   /RF_A
#     L3.2   56.58   /RF_B   C9.1  78.38,56.9   shunt, /RF_B
#     L4.1   55.62   /RF_B   C9.2  79.02,56.9   -> via -> B.Cu -> NT2
#     L4.2   54.98   /ANT_FEED
#     AE1.1  51.5..43.5      C11.1 74.58,55.3   shunt, /ANT_FEED
#                            C11.2 75.22,55.3   -> via -> In1.Cu plane
#
# U1.31 to the ground-plane edge at y = 51.5 is 8.579 mm, against lambda/8 =
# 8.6 mm at 2.4 GHz in FR4. No vias anywhere on the RF nets.
#
# The trace leaves pin 31 at pad width and flares to 0.38 mm past the pad row:
# a 0.38 mm trace on 0.4 mm pitch would sit 0.108 mm from pins 30 and 32, under
# the fab floor. See the QFNEscape rules in the .kicad_dru.
# --------------------------------------------------------------------------
RF = [
    # net,          layer, width,  points
    ("/ANT",        F, 0.2032, [(76.80, 60.079), (76.80, 59.30)]),   # neck out of the pad row
    ("/ANT",        F, 0.38,   [(76.80, 59.30),  (76.80, 58.82)]),   # flare, into L2.1

    ("/RF_A",       F, 0.38,   [(76.80, 58.18),  (76.80, 57.22)]),   # L2.2 -> L3.1
    ("/RF_A",       F, 0.38,   [(74.58, 58.50),  (74.58, 57.70),
                                (76.80, 57.70)]),                    # C6.1 shunt into the node

    ("/RF_B",       F, 0.38,   [(76.80, 56.58),  (76.80, 55.62)]),   # L3.2 -> L4.1
    ("/RF_B",       F, 0.38,   [(78.38, 56.90),  (78.38, 56.10),
                                (76.80, 56.10)]),                    # C9.1 shunt into the node

    ("/ANT_FEED",   F, 0.38,   [(76.80, 54.98),  (76.80, 51.60)]),   # L4.2 -> AE1 feed pad
    ("/ANT_FEED",   F, 0.38,   [(74.58, 55.30),  (74.58, 54.50),
                                (76.80, 54.50)]),                    # C11.1 shunt into the node
]

# C6's ground reaches pin 32 and nothing else, on F.Cu, with no via - Nordic
# rule 1. It then reaches the centre pad through NT1, whose pads physically
# overlap U1.32 and U1.49, so the tie needs no copper of its own.
# The last hop necks to 0.3 mm because pad 32 is 0.1968 mm from pin 31 by pitch.
# Pin 33 (DECA) sits immediately left of pad 32 at x = 76.0, so the return
# cannot cut diagonally across the pad row - it runs ABOVE the row and drops
# straight onto pad 32 through the 0.1968 mm gap between pins 33 and 31.
# Pin 33 (DECA) sits immediately left of pad 32, so the corridor to pad 32 is
# only 0.597 mm wide (pin 33 right edge 76.1016 to pin 31 left edge 76.6984),
# and the 0.38 mm RF flare eats 0.088 mm of it. So the return runs ABOVE the pad
# row at full 0.4 mm width, then necks to 0.18 mm for the last 0.5 mm and drops
# onto pad 32 below the flare. 0.18 mm carries nothing - it is a decoupling
# return, not a current path.
GND_PA = [
    ("/GND_PA",     F, 0.40,   [(75.22, 58.50),  (76.20, 59.30)]),
    ("/GND_PA",     F, 0.18,   [(76.20, 59.30),  (76.36, 59.55)]),
    ("/GND_PA",     F, 0.18,   [(76.36, 59.55),  (76.36, 59.80)]),
]

# C9's ground reaches the BOTTOM layer only - Nordic rule 2 - where NT2 ties it
# to GND. The short F.Cu stub down to the via is the unavoidable part.
GND_C9 = [
    ("/GND_C9",     F, 0.40,   [(79.02, 56.90),  (79.60, 56.30)]),
    ("/GND_C9",     B, 0.40,   [(79.60, 56.30),  (80.30, 55.20)]),
]

# C11's ground is plain GND and goes straight down to the In1.Cu plane.
# AE1's shorting stub likewise: its pad ends exactly on the plane edge, so it
# drops through the AntennaCrossing window at x 72.2-73.4.
GND_RF = [
    ("GND",         F, 0.40,   [(75.22, 55.30),  (75.22, 56.20)]),
    ("GND",         F, 0.60,   [(72.80, 51.35),  (72.80, 51.95)]),
]

# NO stitching vias along the RF run, and this is deliberate.
#
# LAYOUT.md section 2 asks for stitching vias "along both sides of the RF trace"
# at <=3 mm (lambda/20). That rule is for coplanar waveguide, where top-side
# ground beside the trace has to be tied down to the reference plane. This board
# is not CPWG: Zone B has exactly ONE ground layer, In1.Cu. F.Cu carries no
# ground pour beside the trace and B.Cu carries none in Zone B either, so a
# stitching via connects to In1.Cu and nothing else. Four were tried and KiCad
# reported all four as via_dangling - connected on only one layer.
#
# That is consistent with the rest of the design: the 0.38 mm width in
# LAYOUT.md section 2 is derived from the MICROSTRIP equation, and for microstrip
# the return current flows in the reference plane directly under the trace. The
# thing that actually has to hold is "unbroken In1.Cu beneath the entire run",
# and ZoneB_GND is continuous from y = 51.5 all the way past U1.
#
# Going CPWG instead would need F.Cu ground either side at a controlled gap, and
# would make 0.38 mm the wrong width. See the note in NEXT-STEPS.md.

VIAS = [
    # x,     y,      net,        size, drill
    (79.60, 56.30, "/GND_C9",    0.60, 0.30),   # C9 ground down to B.Cu / NT2
    (75.22, 56.20, "GND",        0.60, 0.30),   # C11 ground into the plane
    (72.80, 51.95, "GND",        0.80, 0.40),   # AE1 shorting stub into the plane
]

ROUTES = RF + GND_PA + GND_C9 + GND_RF


# --------------------------------------------------------------------------

def mm(v):
    return pcbnew.FromMM(v)


def pt(xy):
    return pcbnew.VECTOR2I(mm(xy[0]), mm(xy[1]))


def netcode(board, name):
    ni = board.FindNet(name)
    if ni is None:
        raise SystemExit(f"net not found on the board: {name!r}")
    return ni.GetNetCode()


def clear_copper(board):
    """Remove every track and via. Leaves graphics, footprints and zones alone."""
    doomed = [t for t in board.GetTracks()]
    for t in doomed:
        board.Remove(t)
    return len(doomed)


def add_track(board, net, layer, width, a, b):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(a))
    t.SetEnd(pt(b))
    t.SetWidth(mm(width))
    t.SetLayer(board.GetLayerID(layer))
    t.SetNetCode(netcode(board, net))
    board.Add(t)


def add_via(board, x, y, net, size, drill, top=F, bottom=B):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt((x, y)))
    v.SetWidth(mm(size))
    v.SetDrill(mm(drill))
    v.SetLayerPair(board.GetLayerID(top), board.GetLayerID(bottom))
    v.SetNetCode(netcode(board, net))
    board.Add(v)


def main():
    check = "--check" in sys.argv
    board = pcbnew.LoadBoard(BOARD)

    removed = clear_copper(board)

    segs = 0
    for net, layer, width, pts in ROUTES:
        for a, b in zip(pts, pts[1:]):
            add_track(board, net, layer, width, a, b)
            segs += 1

    for x, y, net, size, drill in VIAS:
        add_via(board, x, y, net, size, drill)

    filler = pcbnew.ZONE_FILLER(board)
    if not filler.Fill(board.Zones()):
        raise SystemExit("zone fill failed")

    out = "/tmp/routed.kicad_pcb" if check else BOARD
    pcbnew.SaveBoard(out, board)
    print(f"removed {removed} existing copper items")
    print(f"added   {segs} segments, {len(VIAS)} vias")
    print(f"wrote   {out}")


if __name__ == "__main__":
    main()
