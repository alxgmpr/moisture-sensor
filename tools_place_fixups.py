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

# ref -> (library, footprint) to swap in before positioning. The generator is
# frozen, so a footprint change has to happen here or not at all.
# ref -> (library, footprint) to swap in before positioning. The generator is
# frozen, so a footprint change has to happen here or not at all. Empty for now
# - see the C27 note below.
SWAPS = {}


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

    # U3 turned 90 deg so its sense pins face the probe. This came out of
    # trying to route /SENSE2 and finding it could not be done at all.
    #
    # THE BLOCKER. U3 is an MSOP-10 with five pads per side. As placed, the
    # sense side was the WEST column at x = 68.9, and the probe is SOUTH:
    #
    #     U3.1 SHLD    (68.90, 107.50)
    #     U3.2 SENSE1  (68.90, 108.00)
    #     U3.3 SENSE2  (68.90, 108.50)
    #     U3.4 CIN3    (68.90, 109.00)   unused, but still copper
    #     U3.5 CIN4    (68.90, 109.50)   unused, but still copper
    #
    # Pads 4 and 5 sit directly below the two sense pins, so nothing can leave
    # southward - both sense nets had to exit west and then turn. The pad
    # column's west edge is x = 68.15 and the guard channel starts at 67.30,
    # which leaves 0.65 mm to carry BOTH of them past the package, and the
    # sense-to-shield rule wants 0.2 mm either side:
    #
    #     0.2 + w + 0.2 + w + 0.2 = 0.65  ->  w = 0.025 mm
    #
    # One 0.25 mm trace fits. Two do not, at any width worth using - dropping
    # both to the 0.127 mm fab floor still lands 0.004 mm short, and a thin
    # high-impedance sense trace is the wrong thing to want anyway.
    #
    # THE FIX. Rotated 90 deg, the sense column becomes the SOUTH row:
    #
    #     U3.1 SHLD    (70.00, 110.60)
    #     U3.2 SENSE1  (70.50, 110.60)
    #     U3.3 SENSE2  (71.00, 110.60)
    #
    # Both sense pins now face the electrodes directly with the whole 10 mm
    # width of the escape corridor in front of them, and no unused pad in the
    # way. The supply and TWI side (pads 6-10) turns to face north, toward the
    # rest of the board, which is where those nets come from.
    #
    # This is the placement equivalent of the L1 and L10 rotations: the quiet
    # nets take the awkward path and the sensitive ones get the short one.
    ("U3", None, 90.0),

    # The three sense test points move 0.5 mm south, because rotating U3 grew
    # its courtyard southward into them:
    #
    #     U3 courtyard   y 105.355 .. 111.645   (was x-wide, now y-tall)
    #     TP courtyard   y 111.454 .. 113.546   at the old y = 112.5
    #
    # DRC reported the TP2 pair; TP1 overlapped as well, by 0.191 mm. At
    # y = 113.0 the test-point courtyards start at 111.954, clearing U3 by
    # 0.309 mm. They stay inside the SenseEscape guard region (y 105.8..112.4)
    # only at their north edge now, which is fine - what matters is that they
    # sit over guard, and ZoneC_GUARD_F starts at y = 112.
    # The DECA bank turned end for end and pulled east. Audit finding 4: C2,
    # C12 and C5 sat 8.17, 8.19 and 8.44 mm from pin 43, where Nordic's own
    # reference layout puts them against the package.
    #
    # Half of that was free. All three had their /DECA pad on the WEST side,
    # pointing AWAY from U1, so the net left the capacitor going in the wrong
    # direction and doubled back - 1.13 mm each, for a rotation.
    #
    # The rest is what the space allows, and it is not much. The band between
    # the bank and the FB1/L1 column is 0.67 mm wide, so each cap can only move
    # until its courtyard meets its neighbour:
    #
    #     C2   blocked by FB1 west edge 68.84  ->  centre 67.50
    #     C12  blocked by L1  west edge 68.31  ->  centre 66.97
    #     C5   same, and it straddles L1's row ->  centre 66.97
    #
    # Together: 8.17 -> 6.04, 8.19 -> 6.59, 8.44 -> 6.90 mm.
    #
    # Nordic gets these against the pins because their reference uses 0201s.
    # A 0402 hand-solder courtyard is 2.28 mm on its long axis and the corridor
    # between the L1/FB1 column and U1 is 1.50 mm, so no orientation of a 0402
    # fits there at all. Closing the remaining ~6 mm means either 0201s for
    # this bank or re-planning the whole west side of U1; it is not a nudge.
    ("C2",  (67.50, 62.60), 180.0),
    ("C12", (66.97, 64.00), 180.0),
    ("C5",  (66.97, 65.40), 180.0),

    # C3, the VDD bulk cap, same story as the DECA bank. Its +3V3 pad was on
    # the WEST side at x = 65.138 while U1.48 is at x = 74.079, so the rail left
    # the capacitor heading away from the part it feeds. Turning it recovers
    # 1.72 mm - a 0603's pads are further apart than an 0402's, so the rotation
    # is worth more here.
    #
    # East is limited by two different neighbours on two different rows: C10's
    # courtyard starts at x = 68.86 and overlaps C3's upper edge, X1's starts at
    # 69.56 and overlaps its lower edge. The binding one is C10, at centre
    # 66.97. Together: 9.43 -> 6.93 mm.
    #
    # Same packaging ceiling as the DECA bank. A 0603 hand-solder courtyard is
    # 3.38 x 1.55 mm and the only gap nearer U1 is 1.51 mm tall, so it does not
    # fit there in any orientation.
    ("C3", (66.97, 68.20), 180.0),

    # X2 stays at 0, and this entry exists to say so deliberately rather than
    # by omission - FIXUPS only SETS orientations, so a part with no entry keeps
    # whatever the board already has.
    #
    # Rotating it was tried, because the FA-128's two crystal terminals sit on a
    # DIAGONAL (pads 1 and 3 are opposite corners) while U1's XC1/XC2 pins are
    # side by side 0.4 mm apart, and that is what makes the two nets different
    # lengths however they are routed. A full sweep at (71.0, 60.0):
    #
    #     rot     XC1     XC2     sum   mismatch
    #       0   5.117   3.758   8.875      1.359   <- kept
    #      90   5.190   3.667   8.857      1.523
    #     135   4.718   4.210   8.928      0.507
    #     180   4.155   4.721   8.875      0.566
    #     315   4.603   4.322   8.925      0.281   <- best on paper
    #
    # 315 deg routed out at 6.10 and 6.08 mm - a 0.03 mm mismatch against 1.52.
    # It was still reverted, for two reasons.
    #
    # It does not route. The other diagonal carries the two GROUND pads, so at
    # any 45 deg rotation a ground pad sits between the approach and the crystal
    # pad it is aimed at. At 315 the XC2 approach dived across U1's own pad row
    # and bridged mask to pins 36 and 37; at 180 it ran straight into pad 2.
    # Both needed a detour long enough to give back what the symmetry won.
    #
    # And the symmetry is not the binding constraint. The load capacitors are
    # internal to the nRF54L15, so a length mismatch only unbalances STRAY
    # capacitance: 1.36 mm at roughly 1.2 pF/cm is about 0.16 pF out of an 8 pF
    # load, which pulls well under 1 ppm against the crystal's own 20 ppm.
    #
    # What does matter is TOTAL length - stray C adds to both sides, pulls
    # frequency and eats startup margin - and rotation cannot help that. Nordic's
    # reference puts the crystal against the package; here the two runs total
    # 8.9 mm. Closing that means moving X2 east, which is blocked in three
    # directions at once (U1's west pad row at x = 74.079, the /DECA run
    # reaching x = 70.60 at y = 61.60, and the XC1/DECA escape lanes at y 58.60
    # and 58.10) and is a placement job for the whole corner, not a rotation.
    ("X2", None, 0.0),

    # C27 onto the tab, across the two rails where they turn around U4.
    # 9.58 -> ~0.6 mm, and the loop U4.3 -> C27 -> U4.4 collapses from
    # something that ran back through the enclosure wall to about 1 mm2.
    #
    # It sits EAST of U4 rather than in the north or south band, because the
    # bands can only reach one rail each: GND leaves along y = 58.90 and +3V3
    # along y = 62.30, on opposite sides of the package. East is where both
    # turn, so it is the only spot that touches both.
    # C27 stays where it is, at 9.58 mm from U4.3, and this is the note saying
    # so on purpose. It was the last outstanding bypass distance and it does not
    # close cleanly.
    #
    # The distance is structural, not a placement oversight: U4 is out on the
    # jut-out THROUGH the enclosure wall and C27 is back inside the box. Three
    # rule areas govern the tab - SHT45_Jut bans pour and vias across all of it,
    # NoCopperSHT45 bans tracks as well under the die - so both rails have to
    # come around U4 from the EAST, and there is exactly one strip where a cap
    # could bridge them:
    #
    #     east strip   x 101.045 .. 102.000  =  0.955 mm
    #     0402 rotated                          1.010 mm  -> does not fit
    #     0201 rotated                          0.790 mm  -> fits
    #
    # A 0201 was tried: swapped in, placed at (101.47, 60.60) rot 90, inside a
    # 0.06 mm window bounded by U4's courtyard on one side and the 0.300 mm
    # board-edge clearance on the other. The placement itself is legal. The
    # ROUTING is not - the two hops onto its pads kept merging with the long tab
    # runs and dragging +3V3 back across U4's pads and into the die keepout,
    # 10 DRC violations including a +3V3/SCL short. Reverted.
    #
    # It is also the weakest case on the board electrically. The SHT45 is an I2C
    # part at 400 kHz drawing microamps idle and ~60 mA only while its heater
    # fires, on millisecond timescales. Roughly 10 nH of loop at those speeds is
    # nothing - unlike C9, where 5 nH flipped a 2.4 GHz shunt inductive.
    #
    # If it is worth closing later: place the 0201 at (101.47, 60.60) rot 90 and
    # draw the two 0.3 mm hops BY HAND, east of x = 101.2 so neither crosses
    # NoCopperSHT45.
    ("TP1", (69.00, 113.00), None),
    ("TP2", (72.00, 113.00), None),
    ("TP3", (75.00, 113.00), None),
]


def main():
    check = "--check" in sys.argv
    board = pcbnew.LoadBoard(BOARD)

    for ref, (lib, name) in SWAPS.items():
        old = board.FindFootprintByReference(ref)
        if old is None:
            raise SystemExit(f"no footprint {ref!r} to swap")
        if old.GetFPIDAsString() == f"{lib}:{name}":
            continue                                  # already swapped
        new = pcbnew.FootprintLoad(
            f"/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/{lib}.pretty",
            name)
        if new is None:
            raise SystemExit(f"could not load {lib}:{name}")
        new.SetReference(ref)
        new.SetValue(old.GetValue())
        new.SetPosition(old.GetPosition())
        new.SetOrientation(old.GetOrientation())
        # carry the nets across by pad name, so routing survives the swap
        nets = {p.GetPadName(): p.GetNet() for p in old.Pads()}
        for p in new.Pads():
            if p.GetPadName() in nets:
                p.SetNet(nets[p.GetPadName()])
        board.Remove(old)
        board.Add(new)
        print(f"  {ref:4s} footprint -> {lib}:{name}")

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
