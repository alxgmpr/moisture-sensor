#!/usr/bin/env python3
"""
Historical zone-generation helper. The production board already contains the
reviewed zones; this script is fail-safe retired so it cannot overwrite that
board. Keep it only as a record of the zone geometry used during the routing
session.

WHY EACH ZONE EXISTS
--------------------
ZoneB_GND_F      F.Cu ground pour over the electronics band. Zone B previously
                 had ground on In1.Cu only, so all 51 F.Cu ground pads needed a
                 via each. The pour collects them; local return vias tie it to
                 In1.Cu, and broader stitching can be added after routing with
                 KiCad's via-stitching zone tool. Kept OUT of the RF corridor.

ZoneB_3V3        In2.Cu +3V3 plane. LAYOUT.md section 1 already assigns In2.Cu
                 the role "power / guard pour"; the guard half exists in Zone C,
                 this is the power half. 21 pads on /+3V3 reach it with one via
                 each instead of a routed spine.

RFPourKeepout    No F.Cu pour beside the controlled-impedance line. LAYOUT.md
                 section 2 records JLCPCB's 0.1565 mm non-coplanar 50 ohm
                 result. Ground on F.Cu would change that geometry; this holds
                 it >= 1.1 mm off the x = 76.8 run.
                 Bans pour only - vias and tracks are unaffected.

SenseNoGround    In1.Cu ground stops above U3. Ground under a sense trace IS
                 measured capacitance (LAYOUT.md section 5), so the plane is
                 carved away over the U3 -> Zone C escape. Stops at x = 73.5 so
                 U3's own ground pin, on the far side of the package, still has
                 plane to via into.

SenseEscape_GUARD / _F
                 Guard, not ground, fills what the carve left. Same net and
                 priority as the Zone C guard zones, which they abut and merge
                 with, extended up to y = 105.8 to cover U3 and the testpoints.
"""

if __name__ == "__main__":
    raise SystemExit(
        "tools_add_zones.py is retired: the production board already contains "
        "the reviewed zones; no board writes are permitted."
    )

import os
import sys

import pcbnew

BOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "nrf-moisture-sensor.kicad_pcb")

# name, net (None = rule area), layers, priority, rect (x1,y1,x2,y2), keepout flags
ZONES = [
    # ---- copper pours -----------------------------------------------------
    # Priorities: the SenseEscape pair abuts ZoneC_GUARD_F (1) and ZoneC_GUARD
    # (0) on the same net, and KiCad requires intersecting zones to differ in
    # priority even when the net matches. Nothing on F.Cu below y = 112.4 is
    # priority 2, so 3 cannot steal area from the SENSE electrodes.
    ("ZoneB_GND_F",  "GND",    ["F.Cu"],            0, (60.40,  53.00, 93.60, 104.00), None),
    # "+3V3", not "/+3V3": the rail is a power SYMBOL in the schematic, which
    # makes it a global net without the root-sheet slash. build() aborts on an
    # unresolvable net rather than silently pouring an unassigned zone.
    ("ZoneB_3V3",    "+3V3",   ["In2.Cu"],          0, (60.40,  53.00, 93.60, 104.50), None),
    ("SenseEscape_GUARD_F", "/SHLD", ["F.Cu"],      3, (67.00, 105.80, 77.00, 112.40), None),
    ("SenseEscape_GUARD",   "/SHLD", ["B.Cu", "In2.Cu"], 1,
                                                      (67.00, 105.80, 77.00, 112.40), None),

    # ---- rule areas (pour only; tracks and vias stay legal) ----------------
    ("RFPourKeepout", None,    ["F.Cu"],            0, (73.90,  52.60, 80.80,  60.75), "pour"),
    ("SenseNoGround", None,    ["In1.Cu"],          0, (66.00, 105.80, 73.50, 114.60), "pour"),

    # ---- fine-pitch fanout windows ----------------------------------------
    # Where the vendor land pattern, not a routing decision, sets how wide a
    # track can be and how close it may sit. Two .kicad_dru rules key off this
    # name; see the comment block there. Deliberately EXCLUDES U1's bottom pad
    # row (y < 60.3), which is where the RF escape lives - that row has its own
    # QFNEscape window and everything else on it escapes at 0.19 mm, which
    # holds 0.2035 mm to its neighbours and needs no exemption.
    # B.Cu ground, local to the RF return. C9's shunt has to reach ground on a
    # layer that is NOT the controlled RF line's reference plane - Nordic's rule 2 - and
    # In1.Cu is the RF reference and In2.Cu is the 3V3 plane, so the return must
    # stay on B.Cu. ZoneB_GND_B gives NT2 a local bottom-layer landing and keeps
    # the return out of the RF reference plane.
    #
    # The short F.Cu stub and via are unavoidable; the B.Cu pour then provides
    # the low-inductance local return to NT2.
    #
    # It starts at x = 78.00, which is 1.20 mm east of the /ANT column at 76.80,
    # so it never sits under the RF trace and the 50 ohm geometry LAYOUT.md
    # section 2 solved for non-coplanar L1-over-L2 is untouched. Three existing
    # stitching vias - (81.50, 55.00), (84.00, 55.00), (86.50, 55.00) - tie it
    # to In1.Cu, all at least 4.70 mm from the trace.
    ("ZoneB_GND_B",  "GND",    ["B.Cu"],            0, (78.00,  51.50, 88.00,  62.00), None),
    ("FinePitchFanout", None,  ["F.Cu"],            0, (74.20,  59.60, 75.05,  60.50), "none"),  # U1 pin 36 only
    # /RF_PA_RETURN_LOCAL's climb from C6 pad 2 to U1 pin 32. It is 0.18 mm wide, not the
    # 0.4 mm the Power class asks for, and the reason is the same as everywhere
    # else here: it runs in a 0.5 mm slot between pin 33's pad at x = 76.102 and
    # L2's pad at x = 76.600. Stops at x = 76.55, short of the /ANT run at
    # 76.62, so the RF keeps its own clearance.
    ("FinePitchFanout", None,  ["F.Cu"],            0, (76.15,  57.60, 76.55,  60.20), "none"),  # /RF_PA_RETURN_LOCAL climb
    ("FinePitchFanout", None,  ["F.Cu"],            0, (72.20,  60.30, 74.50,  65.70), "none"),  # U1 left
    ("FinePitchFanout", None,  ["F.Cu"],            0, (74.50,  65.30, 79.50,  67.00), "none"),  # U1 top
    ("FinePitchFanout", None,  ["F.Cu"],            0, (79.50,  60.30, 81.10,  65.70), "none"),  # U1 right
    ("FinePitchFanout", None,  ["F.Cu"],            0, (66.10,  92.00, 72.90,  99.40), "none"),  # U2
    # U3, digital side. Moved when U3 was rotated 90 deg to face the probe
    # (tools_place_fixups.py): the supply and TWI pins used to be the EAST
    # column at x = 73.1 and are now the NORTH row at y = 106.4, so the old
    # window at (71.90, 106.90)-(75.00, 110.10) covered bare board. Nothing
    # complains about a rule area in the wrong place - it just stops exempting
    # what it was drawn for, and the GND escape started failing the 0.4 mm
    # Power width rule instead.
    ("FinePitchFanout", None,  ["F.Cu"],            0, (69.60, 105.20, 72.50, 107.30), "none"),  # U3, digital side
    # U3, sense side. CIN1 and CIN2 are adjacent pins on a 0.5 mm pitch, so the
    # two channels leave the package 0.5 mm apart and no amount of routing
    # changes that - the "Sense channel to sense channel" rule asks for 0.6 mm
    # and cannot be met at the pad. The window covers the escape only, as far
    # as y = 112.20 where the two nets diverge; past it the full 0.6 mm holds.
    ("FinePitchFanout", None,  ["F.Cu"],            0, (69.60, 109.70, 72.50, 112.20), "none"),  # U3, sense side
]


def mm(v):
    return pcbnew.FromMM(v)


def build(board, name, net, layers, prio, rect, keepout):
    z = pcbnew.ZONE(board)
    z.SetZoneName(name)

    ls = pcbnew.LSET()
    for ln in layers:
        lid = board.GetLayerID(ln)
        if lid < 0:
            raise SystemExit(f"{name}: unknown layer {ln!r}")
        ls.addLayer(lid)
    z.SetLayerSet(ls)

    if net is not None:
        ni = board.FindNet(net)
        if ni is None or not hasattr(ni, "GetNetCode"):
            raise SystemExit(f"{name}: net lookup failed for {net!r}")
        z.SetNetCode(ni.GetNetCode())

    z.SetAssignedPriority(prio)
    z.SetMinThickness(mm(0.2))
    z.SetLocalClearance(mm(0.25))
    # Solid, not thermal relief. Thermal spokes cannot resolve two-per-pad on
    # the QFN ground pins - the neighbouring pads
    # block them, which DRC reports as starved_thermal - and a spoke in series
    # with a QFN ground pin is inductance this board does not want. Solid also
    # matches "solid unbroken ground" in LAYOUT.md section 4. The cost is
    # hand-soldering difficulty on GND pads.
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    # Drop unconnected islands rather than leave floating copper to explain.
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)

    if keepout:
        # "none" is a rule area that forbids nothing - it exists only so the
        # .kicad_dru can name the region with insideArea().
        z.SetIsRuleArea(True)
        z.SetDoNotAllowZoneFills(keepout == "pour")
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)

    x1, y1, x2, y2 = rect
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        ol.Append(mm(x), mm(y))

    board.Add(z)
    return z


def main():
    raise SystemExit(
        "tools_add_zones.py is retired: the production board already contains "
        "the reviewed zones; no board writes are permitted."
    )

    check = "--check" in sys.argv
    board = pcbnew.LoadBoard(BOARD)

    wanted = {n for n, *_ in ZONES}
    doomed = [z for z in board.Zones() if z.GetZoneName() in wanted]
    for z in doomed:
        board.Remove(z)

    for spec in ZONES:
        build(board, *spec)

    filler = pcbnew.ZONE_FILLER(board)
    if not filler.Fill(board.Zones()):
        raise SystemExit("zone fill failed")

    out = "/tmp/zoned.kicad_pcb" if check else BOARD
    pcbnew.SaveBoard(out, board)
    print(f"replaced {len(doomed)} existing, added {len(ZONES)} zones")
    for z in board.Zones():
        if z.GetZoneName() in wanted:
            print(f"  {z.GetZoneName():22s} net={z.GetNetname()!r:8s} "
                  f"rule={z.GetIsRuleArea()} prio={z.GetAssignedPriority()}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
