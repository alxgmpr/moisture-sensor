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
# The trace leaves pin 31 at pad width and flares to 0.36 mm past the pad row:
# a wide trace on 0.4 mm pitch would sit ~0.11 mm from pins 30 and 32, under the
# fab floor. See the QFNEscape rules in the .kicad_dru.
#
# 0.36 mm is JLCPCB's OWN solver output - 14.12 mil for 50 ohm single-ended on
# L1 referenced to L2 in the JLC04161H-7628 stackup, read off their impedance
# calculator, not derived here. See LAYOUT.md section 2.
# --------------------------------------------------------------------------
RF = [
    # net,          layer, width,  points
    ("/ANT",        F, 0.2032, [(76.80, 60.079), (76.80, 59.30)]),   # neck out of the pad row
    ("/ANT",        F, 0.36,   [(76.80, 59.30),  (76.80, 58.82)]),   # flare, into L2.1

    ("/RF_A",       F, 0.36,   [(76.80, 58.18),  (76.80, 57.22)]),   # L2.2 -> L3.1
    ("/RF_A",       F, 0.36,   [(74.58, 58.50),  (74.58, 57.70),
                                (76.80, 57.70)]),                    # C6.1 shunt into the node

    ("/RF_B",       F, 0.36,   [(76.80, 56.58),  (76.80, 55.62)]),   # L3.2 -> L4.1
    ("/RF_B",       F, 0.36,   [(78.38, 56.90),  (78.38, 56.10),
                                (76.80, 56.10)]),                    # C9.1 shunt into the node

    ("/ANT_FEED",   F, 0.36,   [(76.80, 54.98),  (76.80, 53.70)]),   # L4.2 -> J5 U.FL signal pad
    ("/ANT_FEED",   F, 0.36,   [(74.58, 55.30),  (74.58, 54.50),
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

# C11's ground goes straight down to the In1.Cu plane. J5's two ground pads sit
# on the Zone A ground pour, which now floods the whole area, so they need no
# routing - just stitching vias to tie the pour through to the inner plane.
GND_RF = [
    ("GND",         F, 0.40,   [(75.22, 55.30),  (75.22, 56.20)]),
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
    (74.60, 52.00, "GND",        0.60, 0.30),   # J5 ground pads -> In1.Cu plane
    (79.00, 52.00, "GND",        0.60, 0.30),
]

# --------------------------------------------------------------------------
# Everything below is routed against PAD REFERENCES, not literal coordinates:
# a waypoint written "U1.36" resolves to that pad's centre at run time. The RF
# section above stays literal because it is verified and measured, and because
# its neck geometry is deliberate to a hundredth of a millimetre.
#
# Anything that reaches a plane does so with a via and no more track than it
# takes to get out of the pad row:
#
#   GND    -> ZoneB_GND_F on F.Cu collects the pads; STITCH ties it to In1.Cu
#   /+3V3  -> ZoneB_3V3 on In2.Cu, one via per pad
#
# so the tables here carry the nets that are genuinely point to point.
# --------------------------------------------------------------------------

# GND pads that the F.Cu pour cannot reach: U3's, because the plane and the
# pour are both carved back over the sense escape; U4's, because the SHT45
# jut-out bans pour and vias entirely; and J5's right-hand ground pad, whose
# stitching via only grazes it.
GND_EXTRA = [
    ("GND",         F, 0.30,   ["U3.7",   (74.60, 109.00)]),          # -> via, In1.Cu
    ("GND",         F, 0.40,   ["J5.2b",  (79.00, 52.00)]),           # -> existing stitch via
    # Out of the jut-out. NoCopperSHT45 is the 0.87 mm gap BETWEEN U4's two pad
    # columns - the SHT4x datasheet 5.3 die keepout - and U4's pads sit 0.03 mm
    # from its edge, so a track leaving from the pad CENTRE puts its end cap and
    # that cap's clearance halo inside the keepout. Both x = 100.5 pads
    # therefore start at their OUTER edge, x = 100.75, and run east before
    # turning. No via anywhere in the tab: SHT45_Jut bans them.
    ("GND",         F, 0.40,   [(100.75, 60.20), (101.20, 60.20), (101.20, 58.90),
                                (93.00, 58.90)]),
]

# /+3V3 down to the In2.Cu plane. One entry per pad; the plane does the rest.
# Necks: 0.19 mm at U1 (0.4 mm pitch) and 0.30 mm at U2 (0.5 mm pitch), which
# is what the FinePitchFanout rules in the .kicad_dru exist for.
V3 = [
    # -- U1, the four QFN escapes ------------------------------------------
    # Pin 36 is the end of the bottom pad row and escapes WEST into the package
    # corner. It still needs a neck, and the reason is the track END CAP, not
    # the track body: a 0.4 mm track leaving pad 36 puts a 0.2 mm radius disc on
    # the pad centre, which is 0.0985 mm from pin 35 - and satisfying the 0.25 mm
    # Power clearance would need the width under 0.097 mm, below the fab floor.
    # So 0.19 mm off the pad, then flare. This is the ONLY bottom-row pin with a
    # FinePitchFanout window; it is 1.75 mm from the /ANT run at x = 76.8, so the
    # RF escape keeps its full clearance. Every other bottom-row pin is Default
    # class, where 0.19 mm holds 0.2035 mm and needs no exemption at all.
    ("/+3V3",       F, 0.19,   ["U1.36",  (74.55, 60.079)]),
    ("/+3V3",       F, 0.40,   [(74.55, 60.079), (73.30, 60.05)]),
    ("/+3V3",       F, 0.19,   ["U1.47",  (73.35, 64.80)]),
    ("/+3V3",       F, 0.40,   [(73.35, 64.80), (72.90, 65.00), (72.60, 65.00)]),
    ("/+3V3",       F, 0.19,   ["U1.48",  (73.35, 65.20)]),
    ("/+3V3",       F, 0.40,   [(73.35, 65.20), (72.90, 65.00)]),
    ("/+3V3",       F, 0.19,   ["U1.10",  (78.40, 66.55)]),
    ("/+3V3",       F, 0.40,   [(78.40, 66.55), (78.40, 67.30)]),
    ("/+3V3",       F, 0.19,   ["U1.22",  (80.70, 61.60)]),
    ("/+3V3",       F, 0.40,   [(80.70, 61.60), (81.20, 61.60)]),

    # -- U2 -----------------------------------------------------------------
    # Pin 12 cannot drop straight south: R20/R21 sit at y 99.68..100.32 and the
    # 0.873 mm gap under the pad row will not take a via plus its clearance. It
    # runs west along y = 99.25 into the space between R20 and R21 instead.
    ("/+3V3",       F, 0.30,   ["U2.12",  (69.25, 99.25), (67.00, 99.25)]),
    ("/+3V3",       F, 0.30,   ["U2.28",  (69.75, 92.80)]),
    ("/+3V3",       F, 0.40,   [(69.75, 92.80), (69.75, 92.50)]),
    ("/+3V3",       F, 0.30,   ["U2.32",  (67.75, 92.80)]),
    ("/+3V3",       F, 0.40,   [(67.75, 92.80), (67.30, 92.50)]),

    # -- decoupling and the rest -------------------------------------------
    ("/+3V3",       F, 0.40,   ["C4.1",   (71.90, 57.40)]),
    ("/+3V3",       F, 0.40,   ["C7.1",   (82.20, 63.50)]),
    ("/+3V3",       F, 0.40,   ["C8.1",   (79.43, 69.30)]),
    ("/+3V3",       F, 0.40,   ["C10.1",  (68.60, 67.40)]),
    ("/+3V3",       F, 0.60,   ["C3.1",   (63.90, 68.20)]),
    ("/+3V3",       F, 0.40,   ["C27.1",  (90.00, 60.60)]),
    ("/+3V3",       F, 0.40,   ["R22.1",  (83.00, 73.50)]),
    ("/+3V3",       F, 0.40,   ["R23.1",  (83.00, 75.00)]),
    ("/+3V3",       F, 0.40,   ["J4.1",   (68.46, 77.30)]),
    ("/+3V3",       F, 0.40,   ["C25.1",  (71.93, 102.50)]),

    # BUCK2 output. L10 -> C24 is the second half of the SW2 loop and stays a
    # direct fat trace; the plane is tapped at C24, the output cap, not at the
    # inductor. Out of the jut-out, U4 pin 3 leaves NORTH before turning west,
    # for the same NoCopperSHT45 reason as pin 4.
    ("/+3V3",       F, 0.60,   ["L10.2",  (64.725, 94.30), (63.60, 95.40),
                                (63.60, 96.20), "C24.1"]),
    ("/+3V3",       F, 0.60,   ["C24.1",  (61.80, 97.00)]),
    ("/+3V3",       F, 0.40,   [(100.75, 61.00), (101.20, 61.00), (101.20, 62.30),
                                (92.60, 62.30)]),
]

ROUTES = RF + GND_PA + GND_C9 + GND_RF + GND_EXTRA + V3

# Vias to the In2.Cu +3V3 plane, one per escape above.
V3_VIAS = [
    (73.30,  60.05, "/+3V3", 0.60, 0.30),   # U1.36
    (72.60,  65.00, "/+3V3", 0.60, 0.30),   # U1.47 + U1.48
    (78.40,  67.30, "/+3V3", 0.60, 0.30),   # U1.10
    (81.20,  61.60, "/+3V3", 0.60, 0.30),   # U1.22
    (67.00,  99.25, "/+3V3", 0.60, 0.30),   # U2.12
    (69.75,  92.50, "/+3V3", 0.60, 0.30),   # U2.28
    (67.30,  92.50, "/+3V3", 0.60, 0.30),   # U2.32
    (71.90,  57.40, "/+3V3", 0.60, 0.30),   # C4
    (82.20,  63.50, "/+3V3", 0.60, 0.30),   # C7
    (79.43,  69.30, "/+3V3", 0.60, 0.30),   # C8
    (68.60,  67.40, "/+3V3", 0.60, 0.30),   # C10
    (63.90,  68.20, "/+3V3", 0.80, 0.40),   # C3, the VDD bulk cap
    (90.00,  60.60, "/+3V3", 0.60, 0.30),   # C27, SHT45 decoupling
    (83.00,  73.50, "/+3V3", 0.60, 0.30),   # R22
    (83.00,  75.00, "/+3V3", 0.60, 0.30),   # R23
    (68.46,  77.30, "/+3V3", 0.60, 0.30),   # J4, SWD header
    (71.93, 102.50, "/+3V3", 0.60, 0.30),   # C25
    (61.80,  97.00, "/+3V3", 0.80, 0.40),   # C24, the BUCK2 output cap
    (92.60,  62.30, "/+3V3", 0.60, 0.30),   # U4, out of the jut-out
]

# GND vias that are not a pad escape.
GND_VIAS = [
    (74.60, 109.00, "GND", 0.60, 0.30),     # U3 ground, past the SenseNoGround carve
    (93.00,  58.90, "GND", 0.60, 0.30),     # U4 ground, out of the jut-out
]

# Stitching. ZoneB_GND_F on F.Cu collects the ground pads; these tie it through
# to the In1.Cu plane. Kept clear of the RF corridor - see the note above.
STITCH = []

ALL_VIAS = VIAS + V3_VIAS + GND_VIAS + [(x, y, "GND", 0.60, 0.30) for x, y in STITCH]


# --------------------------------------------------------------------------

def mm(v):
    return pcbnew.FromMM(v)


def pt(xy):
    return pcbnew.VECTOR2I(mm(xy[0]), mm(xy[1]))


def pad_map(board):
    """Resolve every "REF.PAD" waypoint to a coordinate, before any mutation.

    J5 has two pads both called "2", so its ground pads are addressed as
    "J5.2a" (left, x = 75.325) and "J5.2b" (right, x = 78.275).
    """
    out = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        seen = {}
        for pad in fp.Pads():
            name = pad.GetPadName()
            p = pad.GetPosition()
            xy = (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))
            key = f"{ref}.{name}"
            if key in out:
                # Duplicate pad number: keep both, ordered left to right.
                seen.setdefault(name, [out.pop(key)]).append(xy)
            else:
                out[key] = xy
        for name, xys in seen.items():
            for i, xy in enumerate(sorted(xys)):
                out[f"{ref}.{name}{chr(ord('a') + i)}"] = xy
    return out


def resolve(pts, pads):
    out = []
    for p in pts:
        if isinstance(p, str):
            if p not in pads:
                raise SystemExit(f"unknown pad reference {p!r}")
            out.append(pads[p])
        else:
            out.append(p)
    return out


def net_map(board):
    """Resolve every net name we route to its net code, BEFORE anything else.

    Two KiCad 10 quirks make this the only reliable order. Nets are stored by
    NAME in the .kicad_pcb with no net-code table, so the board object is the
    only source; and calling board.Remove() on the existing tracks invalidates
    the NETINFO wrappers, so FindNet() afterwards hands back an unusable
    SwigPyObject. Resolve first, mutate second.
    """
    names = {n for n, _, _, _ in ROUTES} | {n for _, _, n, _, _ in ALL_VIAS}
    out = {}
    for name in sorted(names):
        ni = board.FindNet(name)
        if ni is None or not hasattr(ni, "GetNetCode"):
            raise SystemExit(f"net lookup failed for {name!r} (got {type(ni).__name__})")
        out[name] = ni.GetNetCode()
    return out


def clear_copper(board):
    """Remove every track and via. Leaves graphics, footprints and zones alone."""
    doomed = [t for t in board.GetTracks()]
    for t in doomed:
        board.Remove(t)
    return len(doomed)


def add_track(board, code, layer, width, a, b):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(a))
    t.SetEnd(pt(b))
    t.SetWidth(mm(width))
    t.SetLayer(board.GetLayerID(layer))
    t.SetNetCode(code)
    board.Add(t)


def add_via(board, x, y, code, size, drill, top=F, bottom=B):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt((x, y)))
    v.SetWidth(mm(size))
    v.SetDrill(mm(drill))
    v.SetLayerPair(board.GetLayerID(top), board.GetLayerID(bottom))
    v.SetNetCode(code)
    board.Add(v)


def main():
    check = "--check" in sys.argv
    board = pcbnew.LoadBoard(BOARD)

    codes = net_map(board)          # must happen before clear_copper()
    pads = pad_map(board)           # ditto - Remove() invalidates the wrappers
    routes = [(n, l, w, resolve(p, pads)) for n, l, w, p in ROUTES]
    removed = clear_copper(board)

    segs = 0
    for net, layer, width, pts in routes:
        for a, b in zip(pts, pts[1:]):
            add_track(board, codes[net], layer, width, a, b)
            segs += 1

    for x, y, net, size, drill in ALL_VIAS:
        add_via(board, x, y, codes[net], size, drill)

    filler = pcbnew.ZONE_FILLER(board)
    if not filler.Fill(board.Zones()):
        raise SystemExit("zone fill failed")

    out = "/tmp/routed.kicad_pcb" if check else BOARD
    pcbnew.SaveBoard(out, board)
    print(f"removed {removed} existing copper items")
    print(f"added   {segs} segments, {len(ALL_VIAS)} vias")
    print(f"wrote   {out}")


if __name__ == "__main__":
    main()
