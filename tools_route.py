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
#     L2.1   58.82
#     L2.2   58.18   /RF_A   C6.1  76.25,57.18  shunt, /RF_A - 0.39 mm to L3.1
#     L3.1   57.22   /RF_A   C6.2  76.25,57.82  -> U1.32, top layer only
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
    ("/RF_A",       F, 0.36,   [(76.10, 57.18),  (76.65, 57.20)]),   # C6.1 shunt, 0.39 mm to L3.1

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
#
# It is now a straight climb up x = 76.36 rather than the old diagonal from
# (75.22, 58.5). C6 was moved under pin 32 for that reason - see the long note
# in tools_place_fixups.py. The diagonal swept through the only corridor U1
# pins 33, 34 and 35 had to escape through, and left pin 33 with no legal
# escape at any width.
#
# Width is 0.20 mm, not 0.40, and it is set by what is either side: pin 33's
# pad at x = 76.102 and the /ANT run at x = 76.62. 76.36 +/- 0.10 holds
# 0.168 mm to the pad and 0.16 mm to /ANT, against the 0.15 mm that QFNEscape
# and MatchingNetwork allow there. The last 0.25 mm necks to 0.18 mm to drop
# onto pad 32 below the RF flare.
GND_PA = [
    ("/GND_PA",     F, 0.18,   [(76.10, 57.82),  (76.35, 58.40)]),
    ("/GND_PA",     F, 0.18,   [(76.35, 58.40),  (76.35, 59.55)]),
    ("/GND_PA",     F, 0.18,   [(76.35, 59.55),  (76.36, 59.80)]),
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
    # 47 and 48 turn SOUTH into the package corner rather than running west,
    # which keeps them off /DCC on pin 46 - it needs 0.3 mm as a SWITCH net and
    # the pins are 0.4 mm apart.
    ("/+3V3",       F, 0.19,   ["U1.47",  (73.35, 64.80), (73.35, 65.55)]),
    ("/+3V3",       F, 0.30,   [(73.35, 65.55), (73.80, 65.90)]),
    ("/+3V3",       F, 0.19,   ["U1.48",  (73.60, 65.45)]),
    ("/+3V3",       F, 0.30,   [(73.60, 65.45), (73.80, 65.90)]),
    ("/+3V3",       F, 0.19,   ["U1.10",  (78.40, 66.55)]),
    ("/+3V3",       F, 0.40,   [(78.40, 66.55), (78.40, 67.30)]),
    ("/+3V3",       F, 0.19,   ["U1.22",  (80.70, 61.60)]),
    ("/+3V3",       F, 0.30,   [(80.70, 61.60), (81.20, 62.30)]),

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
    ("/+3V3",       F, 0.40,   ["R22.1",  (82.40, 73.50)]),
    ("/+3V3",       F, 0.40,   ["R23.1",  (82.40, 75.00)]),
    ("/+3V3",       F, 0.40,   ["J4.1",   (68.46, 77.40), (66.90, 78.00)]),
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


# ------------------------------------------------------------------- MCU ---
# The left column fans out at 0.19 mm, which holds 0.2035 mm to the neighbouring
# pad - inside the FinePitchFanout window, and above the 0.2 mm Default
# clearance anyway. It has to be 0.19 mm and not wider: pin 47 (/+3V3, Power)
# sits next to pin 46 (/DCC, SWITCH, 0.3 mm), and 0.298 - w/2 >= 0.3 has no
# solution at any positive width. That is the package, not the routing.
#
# The bottom row escapes through the corridor C6 vacated - three lanes at
# y = 58.30, 58.70 and 59.10, nested so the net that travels furthest west
# (/DECA) takes the outermost one and turns north clear of the others.
MCU = [
    # -- DC/DC filter: DCC -> L1 -> DECD -> FB1 -> DECA ---------------------
    # /DCC only flares to its 0.5 mm SWITCH width at x = 73.10, by which point
    # /+3V3 from pin 47 has turned south and is out of the way.
    ("/DCC",    F, 0.19, ["U1.46", (72.50, 64.40)]),
    ("/DCC",    F, 0.50, [(72.50, 64.40), (72.20, 64.40), "L1.1"]),

    # /DECD takes the detour over L1 - 1.005 mm of corridor between FB1 and L1,
    # which a 0.3 mm Default-class track fits and a 0.5 mm SWITCH one does not.
    ("/DECD",   F, 0.19, ["U1.45", (72.95, 64.00)]),
    ("/DECD",   F, 0.30, [(72.95, 64.00), (72.60, 63.40), (72.40, 63.30),
                          (69.90, 63.30), "FB1.1"]),
    ("/DECD",   F, 0.30, ["FB1.1", (69.125, 63.30), "L1.2"]),
    ("/DECD",   F, 0.30, ["L1.2", (69.30, 65.60), "C1.1"]),

    # /DECA reaches U1 twice - pin 43 on the left column and pin 33 (DECRF) in
    # the bottom row. Pin 33 is the one C6 had to move for.
    ("/DECA",   F, 0.19, ["U1.43", (73.35, 63.20)]),
    ("/DECA",   F, 0.25, [(73.35, 63.20), (72.60, 62.80), (71.50, 62.70), "FB1.2"]),
    # Pin 33 has to clear /GND_PA's climb before it turns, so it runs west at
    # y = 58.55 for the first millimetre and only then drops to its own lane.
    ("/DECA",   F, 0.19, ["U1.33", (76.00, 58.45)]),
    ("/DECA",   F, 0.20, [(76.00, 58.45), (75.20, 58.45), (74.60, 58.10),
                          (68.80, 58.10)]),
    ("/DECA",   F, 0.25, [(68.80, 58.10), (68.80, 61.60)]),
    ("/DECA",   F, 0.25, [(68.80, 61.60), (70.60, 61.60), (70.60, 62.40), "FB1.2"]),
    ("/DECA",   F, 0.25, [(68.80, 61.60), (66.20, 61.60), (66.00, 62.40), "C2.1"]),
    ("/DECA",   F, 0.25, ["C2.1", (65.20, 62.60), (65.20, 65.40), "C5.1"]),
    ("/DECA",   F, 0.25, [(65.20, 64.00), "C12.1"]),

    # -- crystals -----------------------------------------------------------
    # X2's pads are a 2x2 with 0.45 mm between columns and 0.3 mm between rows,
    # so nothing threads between them: /XC1 has to reach the bottom-left pad
    # from outside, which it does by running west above X2 and dropping at
    # x = 69.50.
    ("/XC1",    F, 0.19, ["U1.34", (75.60, 58.90)]),
    ("/XC1",    F, 0.20, [(75.60, 58.90), (72.00, 58.75), (69.50, 58.75),
                          (69.50, 60.575), "X2.1"]),
    ("/XC2",    F, 0.19, ["U1.35", (75.20, 59.35)]),
    ("/XC2",    F, 0.20, [(75.20, 59.35), (71.475, 59.40), "X2.3"]),

    ("/XL1",    F, 0.19, ["U1.1", (74.80, 66.90)]),
    ("/XL1",    F, 0.25, [(74.80, 66.90), (72.20, 68.10), (70.80, 68.10), "X1.1"]),
    ("/XL2",    F, 0.19, ["U1.2", (75.20, 67.40)]),
    ("/XL2",    F, 0.25, [(75.20, 67.40), (73.20, 68.70), "X1.2"]),

    # -- reset --------------------------------------------------------------
    # Pin 30 sits between the /ANT escape and pin 29, so it leaves at x = 77.25
    # rather than straight down: 0.175 mm to the /ANT flare and 0.153 mm to pin
    # 29, both inside the QFNEscape window.
    ("/NRESET", F, 0.19, ["U1.30", (77.25, 59.40)]),
    ("/NRESET", F, 0.25, [(77.25, 59.40), (77.80, 58.30), (82.00, 58.30), "R1.1"]),
    ("/NRESET", F, 0.25, [(82.00, 58.30), "C13.1"]),

    # -- SWD, PMIC_INT: the B.Cu debug bus ---------------------------------
    # B.Cu is empty across Zone B, so the five long runs go there rather than
    # fight the F.Cu ground pour. They reference the In2.Cu +3V3 plane 0.21 mm
    # below, which is a fine AC return for SWD.
    #
    # Five parallel lanes down the east side at 0.7 mm pitch, peeling west one
    # at a time BELOW J4. The order is forced and it is worth stating: after a
    # lane turns west it runs north to its via, and that northward leg crosses
    # any shallower horizontal whose span covers it. So the shallowest peel must
    # have the EASTERNMOST destination, and the lane order west to east has to
    # match the peel order top to bottom:
    #
    #   lane 83.0  SWO       peels y 78.6 -> x 73.54   (J4 pin 6)
    #   lane 83.7  SWDCLK    peels y 79.3 -> x 72.27   (J4 pin 4)
    #   lane 84.4  SWDIO     peels y 80.0 -> x 69.73   (J4 pin 2)
    #   lane 85.6  SWD_RST   peels y 80.7 -> x 68.20   (J4 pin 10)
    #   lane 86.6  PMIC_INT  runs on to y 101.5        (U2 pin 8)
    #
    # J4 is a Tag-Connect with no legs, so its signal pads are F.Cu only and
    # B.Cu passes straight under the connector - only the three NPTH alignment
    # holes have to be cleared. Pins 6 and 10 are approached from the NORTH
    # because pins 5 and 9 (both GND) sit directly south of them.
    ("/SWDIO",  F, 0.19, ["U1.25", (79.20, 59.30)]),
    ("/SWDIO",  F, 0.20, [(79.20, 59.30), (79.20, 59.00)]),
    ("/SWDIO",  B, 0.25, [(79.20, 59.00), (79.20, 57.40), (84.40, 57.40),
                          (84.40, 80.00), (69.73, 80.00), (69.73, 78.00)]),
    ("/SWDIO",  F, 0.25, [(69.73, 78.00), "J4.2"]),

    ("/SWDCLK", F, 0.19, ["U1.26", (78.80, 59.45)]),
    ("/SWDCLK", F, 0.20, [(78.80, 59.45), (78.30, 59.00)]),
    ("/SWDCLK", B, 0.25, [(78.30, 59.00), (79.00, 59.70), (83.00, 59.70),
                          (83.70, 60.40), (83.70, 79.30), (72.27, 79.30),
                          (72.27, 78.20)]),
    ("/SWDCLK", F, 0.25, [(72.27, 78.20), "J4.4"]),

    ("/P2.07_SWO", F, 0.19, ["U1.18", (80.70, 63.20)]),
    ("/P2.07_SWO", F, 0.20, [(80.70, 63.20), (81.00, 63.20)]),
    ("/P2.07_SWO", B, 0.25, [(81.00, 63.20), (83.00, 65.20), (83.00, 78.60),
                             (73.54, 78.60), (73.54, 73.90)]),
    ("/P2.07_SWO", F, 0.25, [(73.54, 73.90), "J4.6"]),

    ("/SWD_RST", F, 0.30, ["R1.2", (85.60, 58.00)]),
    ("/SWD_RST", B, 0.25, [(85.60, 58.00), (85.60, 80.70), (68.20, 80.70),
                           (68.20, 74.00), (68.46, 73.60)]),
    ("/SWD_RST", F, 0.25, [(68.46, 73.60), "J4.10"]),

    # PMIC_INT joins the bus from the FAR side. Its via would otherwise have to
    # cross all four SWD lanes to reach the east edge, so it runs east on F.Cu
    # at y = 60.60 - under C13, over R1, clear of C7 - and drops to B.Cu at
    # x = 86.90, east of every lane.
    ("/PMIC_INT", F, 0.19, ["U1.23", (80.90, 61.20)]),
    ("/PMIC_INT", F, 0.25, [(80.90, 61.20), (81.40, 60.60), (86.90, 60.60)]),
    ("/PMIC_INT", B, 0.25, [(86.90, 60.60), (86.90, 101.50),
                            (66.00, 101.50), (65.50, 99.00), (65.80, 97.75)]),
    ("/PMIC_INT", F, 0.30, [(65.80, 97.75), "U2.8"]),
]

MCU_VIAS = [
    (79.20, 59.00, "/SWDIO",     0.60, 0.30),
    (69.73, 78.00, "/SWDIO",     0.60, 0.30),
    (78.30, 59.00, "/SWDCLK",    0.60, 0.30),
    (72.27, 78.20, "/SWDCLK",    0.60, 0.30),
    (81.00, 63.20, "/P2.07_SWO", 0.60, 0.30),
    (73.54, 73.90, "/P2.07_SWO", 0.60, 0.30),
    (85.60, 58.00, "/SWD_RST",   0.60, 0.30),
    (68.46, 73.60, "/SWD_RST",   0.60, 0.30),
    (86.90, 60.60, "/PMIC_INT",  0.60, 0.30),
    (65.80, 97.75, "/PMIC_INT",  0.60, 0.30),
]

ROUTES = RF + GND_PA + GND_C9 + GND_RF + GND_EXTRA + V3 + MCU

# Vias to the In2.Cu +3V3 plane, one per escape above.
V3_VIAS = [
    (73.30,  60.05, "/+3V3", 0.60, 0.30),   # U1.36
    (73.80,  65.90, "/+3V3", 0.60, 0.30),   # U1.47 + U1.48
    (78.40,  67.30, "/+3V3", 0.60, 0.30),   # U1.10
    (81.20,  62.30, "/+3V3", 0.60, 0.30),   # U1.22
    (67.00,  99.25, "/+3V3", 0.60, 0.30),   # U2.12
    (69.75,  92.50, "/+3V3", 0.60, 0.30),   # U2.28
    (67.30,  92.50, "/+3V3", 0.60, 0.30),   # U2.32
    (71.90,  57.40, "/+3V3", 0.60, 0.30),   # C4
    (82.20,  63.50, "/+3V3", 0.60, 0.30),   # C7
    (79.43,  69.30, "/+3V3", 0.60, 0.30),   # C8
    (68.60,  67.40, "/+3V3", 0.60, 0.30),   # C10
    (63.90,  68.20, "/+3V3", 0.80, 0.40),   # C3, the VDD bulk cap
    (90.00,  60.60, "/+3V3", 0.60, 0.30),   # C27, SHT45 decoupling
    (82.40,  73.50, "/+3V3", 0.60, 0.30),   # R22 - clear of the B.Cu debug bus
    (82.40,  75.00, "/+3V3", 0.60, 0.30),   # R23
    (66.90,  78.00, "/+3V3", 0.60, 0.30),   # J4, clear of the B.Cu bus at x = 68.2
    (71.93, 102.50, "/+3V3", 0.60, 0.30),   # C25
    (61.80,  97.00, "/+3V3", 0.80, 0.40),   # C24, the BUCK2 output cap
    (92.60,  62.30, "/+3V3", 0.60, 0.30),   # U4, out of the jut-out
]

# GND vias that are not a pad escape.
GND_VIAS = [
    (74.60, 109.00, "GND", 0.60, 0.30),     # U3 ground, past the SenseNoGround carve
    (93.00,  58.90, "GND", 0.60, 0.30),     # U4 ground, out of the jut-out
]

# ---------------------------------------------------------------------------
# Centre-pad via arrays under U1 pad 49 and U2 pad 33. Neither vendor footprint
# has them; Nordic's QFAA reference layout (sheet 3, In1) uses a 4x4 grid under
# the QFN48 centre pad, which is what U1 gets here.
#
#   U1  4x4 at 1.2 mm pitch, offsets +/-0.6 and +/-1.8 from (77.000, 63.000).
#       The pad is 4.6 mm, so the outermost via annulus stops 0.2 mm inside the
#       pad edge.
#   U2  3x3 at 1.2 mm pitch about (69.500, 96.000). The pad is 3.5 mm; 4x4 at
#       1.0 mm would put the outer annulus past the pad edge.
#
# 0.3 mm drill on 1.2 mm pitch leaves 0.9 mm hole to hole against the 0.5 mm
# minimum. ORDER THE BOARD WITH VIAS TENTED - the paste apertures are already
# window-paned to 66 % coverage (NEXT-STEPS.md), and untented vias under a
# thermal pad wick solder out of the joint.
#
# NT1 is the thing to watch. Its GND pad sits at (76.400, 60.705), overlapping
# pad 49's top edge, and its /GND_PA pad at (76.400, 60.405) is 0.345 mm from
# the nearest via in the array. The array is GND throughout and touches
# /GND_PA nowhere, so the tie stays the only bridge between them.
def _grid(cx, cy, offs):
    return [(round(cx + dx, 3), round(cy + dy, 3)) for dy in offs for dx in offs]

CENTRE_PAD = (_grid(77.000, 63.000, (-1.8, -0.6, 0.6, 1.8))     # U1 pad 49
              + _grid(69.500, 96.000, (-1.2, 0.0, 1.2)))         # U2 pad 33

# Stitching. ZoneB_GND_F on F.Cu collects the ground pads; these tie it through
# to the In1.Cu plane. Generated on a 2.5 mm grid and then filtered against
# every pad, body and route on the board - see tools_stitch_gen.py, which
# prints this list.
STITCH = CENTRE_PAD + [
    # 109 stitching vias, 2.5 mm grid
    ( 61.50,  55.00), ( 64.00,  55.00), ( 66.50,  55.00), ( 69.00,  55.00),
    ( 71.50,  55.00), ( 81.50,  55.00), ( 84.00,  55.00), ( 86.50,  55.00),
    ( 89.00,  55.00), ( 91.50,  55.00), ( 61.50,  57.50), ( 64.00,  57.50),
    ( 66.50,  57.50), ( 89.00,  57.50), ( 91.50,  57.50), ( 61.50,  60.00),
    ( 64.00,  60.00), ( 66.50,  60.00), ( 89.00,  60.00), ( 61.50,  62.50),
    ( 64.00,  62.50), ( 89.00,  62.50), ( 91.50,  62.50), ( 61.50,  65.00),
    ( 64.00,  65.00), ( 81.50,  65.00), ( 89.00,  65.00), ( 91.50,  65.00),
    ( 61.50,  67.50), ( 76.50,  67.50), ( 89.00,  67.50), ( 91.50,  67.50),
    ( 61.50,  70.00), ( 64.00,  70.00), ( 66.50,  70.00), ( 74.00,  70.00),
    ( 76.50,  70.00), ( 81.50,  70.00), ( 89.00,  70.00), ( 91.50,  70.00),
    ( 61.50,  72.50), ( 64.00,  72.50), ( 66.50,  72.50), ( 69.00,  72.50),
    ( 71.50,  72.50), ( 74.00,  72.50), ( 76.50,  72.50), ( 79.00,  72.50),
    ( 81.50,  72.50), ( 89.00,  72.50), ( 91.50,  72.50), ( 61.50,  75.00),
    ( 64.00,  75.00), ( 79.00,  75.00), ( 89.00,  75.00), ( 91.50,  75.00),
    ( 61.50,  77.50), ( 64.00,  77.50), ( 79.00,  77.50), ( 81.50,  77.50),
    ( 89.00,  77.50), ( 91.50,  77.50), ( 89.00,  80.00), ( 91.50,  80.00),
    ( 71.50,  82.50), ( 74.00,  82.50), ( 76.50,  82.50), ( 79.00,  82.50),
    ( 71.50,  85.00), ( 74.00,  85.00), ( 76.50,  85.00), ( 79.00,  85.00),
    ( 81.50,  85.00), ( 84.00,  85.00), ( 71.50,  87.50), ( 74.00,  87.50),
    ( 76.50,  87.50), ( 79.00,  87.50), ( 81.50,  87.50), ( 84.00,  87.50),
    ( 71.50,  90.00), ( 74.00,  90.00), ( 76.50,  90.00), ( 61.50,  92.50),
    ( 79.00,  92.50), ( 81.50,  92.50), ( 91.50,  92.50), ( 61.50,  95.00),
    ( 79.00,  95.00), ( 81.50,  95.00), ( 84.00,  95.00), ( 89.00,  95.00),
    ( 91.50,  95.00), ( 79.00,  97.50), ( 84.00,  97.50), ( 89.00,  97.50),
    ( 91.50,  97.50), ( 61.50, 100.00), ( 71.50, 100.00), ( 79.00, 100.00),
    ( 81.50, 100.00), ( 84.00, 100.00), ( 61.50, 102.50), ( 64.00, 102.50),
    ( 66.50, 102.50), ( 69.00, 102.50), ( 79.00, 102.50), ( 81.50, 102.50),
    ( 84.00, 102.50),
]

ALL_VIAS = VIAS + V3_VIAS + GND_VIAS + MCU_VIAS + [(x, y, "GND", 0.60, 0.30) for x, y in STITCH]


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
