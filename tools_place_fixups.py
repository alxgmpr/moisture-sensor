#!/usr/bin/env python3
"""
Placement changes made after tools_gen_pcb.py was frozen.

The generator is frozen because it redraws graphics, so placement now lives in
the .kicad_pcb. This script records the edits that were made to it by hand, so
they are reproducible and so the reason survives. Idempotent: it sets absolute
positions and orientations, it does not nudge.

    $PY tools_place_fixups.py            # edit the board
    $PY tools_place_fixups.py --check    # write to /tmp instead
"""

import os
import sys

import pcbnew

BOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "moisture-sensor-carrier.kicad_pcb")

# ref, (x, y) or None to leave alone, orientation degrees or None
FIXUPS = [
    # L1 turned end for end. It was placed with pad 1 (/DCC) at x = 69.125, the
    # far side from U1, which put the SWITCHING node on the long path: /DCC
    # would have had to get from U1 pin 46 around a 1.75 mm inductor to reach
    # it, and the only corridors are 1.005 mm above L1 and 1.115 mm below,
    # against the 0.5 mm width plus 0.3 mm each side that the SWITCH class
    # needs - 1.1 mm. Both are unroutable or within 0.015 mm of it.
    #
    # Rotated, pad 1 faces U1 and /DCC is a straight 3.2 mm run at full width,
    # while /DECD - a DC node in the Default class, 0.3 mm wide with 0.2 mm
    # clearance - takes the detour above L1 with room to spare. The quiet node
    # gets the awkward path and the switching node gets the short one, which is
    # also what Nordic's QFAA reference layout does.
    ("L1", None, 180.0),

    # C6 turned on its side and moved under pin 32. This one came out of trying
    # to route, and it is a real find rather than a routing convenience.
    #
    # THE BLOCKER. U1 pins 33 (DECRF), 34 (XC1) and 35 (XC2) all have to escape
    # westward, and the only corridor is the band between C6 and the bottom pad
    # row. Two things closed it:
    #
    #   width     over C6's x span the band was 0.998 mm, and after 0.15 mm to
    #             C6 and 0.2 mm to the pad row that is two 0.127 mm lanes, not
    #             three
    #   crossing  worse, /GND_PA ran as a diagonal from C6.2 at (75.22, 58.5)
    #             up to pad 32 at (76.4, 60.079), sweeping through the whole
    #             corridor. Solving the point-to-line distance for pin 33 at
    #             x = 76.0 gives a legal 0.15 mm track only at y >= 59.814 or
    #             y <= 58.459 - the first is inside the pad row, the second is
    #             on the far side of /GND_PA. Pin 33 had NO legal escape at all.
    #
    # The crossing is structural, not a width problem: C6's ground pad has to
    # reach pin 32, and unless it sits directly under pin 32 that return path
    # separates pins 33/34/35 from everything below them.
    #
    # THE FIX. C6 rotated 270 deg so its pads stack vertically - pad 1 (/RF_A)
    # low, pad 2 (/GND_PA) high - and placed at (76.10, 57.50), in the 0.91 mm
    # gap between L3 and L2. /GND_PA becomes a straight 2.0 mm run up x = 76.36
    # instead of a diagonal across the corridor, and the corridor opens from
    # y 57.7 to 59.698 - room for all three lanes plus margin.
    #
    # AND IT FIXES AN RF ERROR THAT WAS ALREADY THERE. C6 is the 1.5 pF shunt on
    # the L2/L3 node at x = 76.8. From (74.58, 58.5) its stub to that node ran
    # 0.8 + 2.22 = 3.02 mm, which is roughly 2 nH in series with the cap:
    #
    #     Z at 2.4 GHz, ideal 1.5 pF        -j44.2 ohm
    #     with 3.02 mm of stub (~2 nH)      +j30.2 - j44.2 = -j14.0 ohm
    #     with 0.39 mm of stub (~0.3 nH)    +j4.5  - j44.2 = -j39.7 ohm
    #
    # A 3x error in the shunt reactance is not a rounding difference; the stub
    # was doing more to the match than the capacitor. Now C6 pad 1 lands 0.39 mm
    # from L3 pad 1 and the shunt is nearly at the node.
    #
    # WHAT IT COSTS. /GND_PA is squeezed between pin 33's pad and the /ANT run,
    # so it narrows from 0.4 mm to 0.2 mm over most of its length: about 2.0 mm
    # of 0.2 mm track, ~1.9 nH, against ~1.2 nH before. Roughly +0.7 nH in the
    # VSS_PA return, traded for taking ~1.7 nH out of the shunt branch and for
    # making the board routable at all. Worth re-checking on the VNA at bring-up
    # along with everything else in the matching network.
    ("C6", (76.10, 57.50), 270.0),

    # L10 turned end for end, for the same reason L1 was and found the same way
    # - by measuring rather than by looking. See docs/audit-2026-07-31.md.
    #
    # /SW2 joins U2 pin 5 to L10 pad 1, and pad 1 was the pad FURTHER from U2:
    #
    #     U2.5   (7.074, 56.250)   board coordinates
    #     L10.1  (3.275, 53.500)   <- SW2 side, far end
    #     L10.2  (4.725, 53.500)   <- VOUT2 side, near end
    #
    # so the highest-dv/dt net on the board ran the length of the inductor body
    # to get to its own pad: 4.69 mm, against 3.62 mm with the part turned
    # round. The BUCK2 loop U2.5 -> L10 -> C24 -> U2.6 measures 5.50 mm2 and
    # 14.43 mm of perimeter as placed.
    #
    # Turning it also costs nothing on the output side. /+3V3 leaves the far pad
    # at x = 3.275 and C24 pad 1 is at x = 3.138, so that run gets shorter too
    # (3.84 -> 3.50 mm). Both halves of the loop improve; there is no trade here.
    #
    # /SW2 has no copper at all yet, so this is free to do now and would have
    # meant ripping up the switch node later.
    ("L10", None, 180.0),
]


def main():
    check = "--check" in sys.argv
    board = pcbnew.LoadBoard(BOARD)

    for ref, pos, rot in FIXUPS:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            raise SystemExit(f"no footprint {ref!r}")
        if pos is not None:
            fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(pos[0]), pcbnew.FromMM(pos[1])))
        if rot is not None:
            fp.SetOrientationDegrees(rot)
        p = fp.GetPosition()
        print(f"  {ref:4s} at ({pcbnew.ToMM(p.x):.3f}, {pcbnew.ToMM(p.y):.3f}) "
              f"rot {fp.GetOrientationDegrees():.1f}")
        for pad in fp.Pads():
            pp = pad.GetPosition()
            print(f"       pad {pad.GetPadName()} {pad.GetNetname():10s} "
                  f"({pcbnew.ToMM(pp.x):.3f}, {pcbnew.ToMM(pp.y):.3f})")

    out = "/tmp/placed.kicad_pcb" if check else BOARD
    pcbnew.SaveBoard(out, board)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
