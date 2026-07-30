#!/usr/bin/env python3
"""Generate the moisture-sensor-carrier board outline, zoning and antenna.

Companion to tools_gen_sch.py. Edit this and re-run; do not hand-edit the
.kicad_pcb. Like the schematic generator it self-checks and aborts rather than
emitting a broken file.

This pass draws geometry only:
  - Edge.Cuts outline (Hammond 1551WK box section + probe stake)
  - four Ø2.6 mounting holes on the 1551WK internal post pattern
  - the three zone boundaries (A antenna / B electronics / C probe)
  - rule areas: AntennaKeepout, ProbeNoGround
  - the PCB inverted-F antenna, placed as a net-tie footprint
  - In1.Cu GND pour bounded to Zone B, guard pours over Zone C

Component placement is a separate pass. Existing footprints are removed
because the board carries stale nets from an earlier schematic revision.

Run:  python3 tools_gen_pcb.py
"""
import sys
import math
import pcbnew

PROJ = "/Users/alex/moisture-sensor-carrier/.claude/worktrees/moisture-sensor-pcb-placement-bff371"
PCB = f"{PROJ}/moisture-sensor-carrier.kicad_pcb"
FPLIB = f"{PROJ}/lib/footprints.pretty"

# ---------------------------------------------------------------- geometry --
# Board-local coordinates: origin is the top-left of the in-enclosure section,
# +X right, +Y down (KiCad convention). ORIGIN maps board-local (0,0) onto the
# sheet.
ORIGIN = (60.0, 40.0)

# -- enclosure: Hammond 1551WK, IP68 polycarbonate -----------------------------
# From the Hammond 1551WKBK drawing (rev 31.08.2023):
#   external 80 x 40 x 22, inside 74.92 x 34.92 x 17.30,
#   MAXIMUM P.C. BOARD 74.50 x 34.50, internal #2 posts on 55.00 x 25.00.
# We take 74.0 x 34.0, i.e. 0.25 mm inside the stated maximum on every side.
BOX_W = 34.0
BOX_L = 74.0
BOX_CORNER_R = 4.5

# Mounting holes on the internal post pattern, centred in the box section.
HOLE_DIA = 2.6
HOLE_PITCH_X = 25.0          # across the width
HOLE_PITCH_Y = 55.0          # along the length
HOLE_KEEPOUT_R = 3.0         # screw head clearance, documentation only

# -- zone boundaries -----------------------------------------------------------
ZONE_A_BOT = 11.5            # ground plane edge. This is part of the antenna.
ZONE_B_BOT = BOX_L           # electronics end where the box ends

# -- probe ---------------------------------------------------------------------
PROBE_W = 20.0
PROBE_X0 = (BOX_W - PROBE_W) / 2.0
PROBE_X1 = PROBE_X0 + PROBE_W
PROBE_FILLET_R = 2.0         # inside fillet at the shoulder
BOARD_L = 155.0
TAPER_TOP = 149.0
TIP_W = 6.0

SOIL_LINE = 115.0            # documentation only, marks the intended depth
SENSE2_Y0, SENSE2_Y1 = 82.0, 112.0      # air reference electrode
SENSE1_Y0, SENSE1_Y1 = 119.0, 149.0     # soil electrode

# -- antenna -------------------------------------------------------------------
# The QFAA reference layout 0.8 contains NO PCB antenna, so this geometry is
# designed for this board rather than copied. Starting point only: tune with the
# enclosure fitted and a realistic soil load. See LAYOUT.md section 3.
IFA_FEED_X = 16.8            # aligns with U1 pin 31 after the 90 deg rotation
IFA_ORIGIN = (IFA_FEED_X, ZONE_A_BOT)

EDGE_W = 0.1
DOC_W = 0.12

# --------------------------------------------------------------------- utils --
def mm(v):
    return pcbnew.FromMM(float(v))


def pt(x, y):
    return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))


def lset(*layers):
    s = pcbnew.LSET()
    for lay in layers:
        try:
            s.addLayer(lay)
        except AttributeError:
            s.AddLayer(lay)
    return s


_errors = []


def check(cond, msg):
    if not cond:
        _errors.append(msg)


# ------------------------------------------------------------------ drawing --
def seg(board, a, b, layer, width=EDGE_W):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(*a))
    s.SetEnd(pt(*b))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)
    return s


def arc(board, a, mid, b, layer, width=EDGE_W):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(pt(*a), pt(*mid), pt(*b))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)
    return s


def circle(board, c, dia, layer, width=EDGE_W):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(pt(*c))
    s.SetEnd(pt(c[0] + dia / 2.0, c[1]))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)
    return s


def text(board, s, at, layer, size=1.0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(pt(*at))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    board.Add(t)
    return t


def ensure_net(board, name):
    """KiCad 10 stores nets by name on the pads, so removing every footprint
    also removes every net. Recreate the handful this pass needs; the placement
    pass replaces the lot from the netlist."""
    net = board.FindNet(name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
    return net


def rule_area(board, name, pts, layers, tracks=False, vias=True, pads=True,
              fills=True, footprints=True):
    """Rule area. The flags say what is DISALLOWED."""
    z = pcbnew.ZONE(board)
    z.SetLayerSet(layers)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowPads(pads)
    z.SetDoNotAllowZoneFills(fills)
    z.SetDoNotAllowFootprints(footprints)
    outline = z.Outline()
    outline.NewOutline()
    for x, y in pts:
        outline.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))
    board.Add(z)
    return z


def pour(board, netname, pts, layers, name):
    z = pcbnew.ZONE(board)
    z.SetLayerSet(layers)
    z.SetZoneName(name)
    net = board.FindNet(netname)
    if net is None:
        _errors.append(f"pour {name}: net {netname} not in board")
        return None
    z.SetNet(net)
    z.SetLocalClearance(mm(0.25))
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    outline = z.Outline()
    outline.NewOutline()
    for x, y in pts:
        outline.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))
    board.Add(z)
    return z


# ------------------------------------------------------------------- outline --
def corner_mid(cx, cy, r, ax, ay, bx, by):
    """Midpoint of the minor arc from (ax,ay) to (bx,by) about (cx,cy)."""
    a0 = math.atan2(ay - cy, ax - cx)
    a1 = math.atan2(by - cy, bx - cx)
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    am = a0 + d / 2.0
    return (cx + r * math.cos(am), cy + r * math.sin(am))


def draw_outline(board):
    R = BOX_CORNER_R
    W, L = BOX_W, BOX_L
    F = PROBE_FILLET_R
    px0, px1 = PROBE_X0, PROBE_X1
    tip0 = (BOX_W - TIP_W) / 2.0
    tip1 = tip0 + TIP_W

    # top edge and the two top corners
    seg(board, (R, 0), (W - R, 0), pcbnew.Edge_Cuts)
    arc(board, (W - R, 0), corner_mid(W - R, R, R, W - R, 0, W, R), (W, R),
        pcbnew.Edge_Cuts)
    seg(board, (W, R), (W, L - R), pcbnew.Edge_Cuts)
    arc(board, (W, L - R), corner_mid(W - R, L - R, R, W, L - R, W - R, L),
        (W - R, L), pcbnew.Edge_Cuts)

    # bottom edge of the box section, right of the probe, with an inside fillet
    seg(board, (W - R, L), (px1 + F, L), pcbnew.Edge_Cuts)
    arc(board, (px1 + F, L),
        corner_mid(px1 + F, L + F, F, px1 + F, L, px1, L + F), (px1, L + F),
        pcbnew.Edge_Cuts)

    # probe, right side down to the taper
    seg(board, (px1, L + F), (px1, TAPER_TOP), pcbnew.Edge_Cuts)
    seg(board, (px1, TAPER_TOP), (tip1, BOARD_L), pcbnew.Edge_Cuts)
    seg(board, (tip1, BOARD_L), (tip0, BOARD_L), pcbnew.Edge_Cuts)
    seg(board, (tip0, BOARD_L), (px0, TAPER_TOP), pcbnew.Edge_Cuts)
    seg(board, (px0, TAPER_TOP), (px0, L + F), pcbnew.Edge_Cuts)

    # inside fillet and bottom edge left of the probe
    arc(board, (px0, L + F),
        corner_mid(px0 - F, L + F, F, px0, L + F, px0 - F, L), (px0 - F, L),
        pcbnew.Edge_Cuts)
    seg(board, (px0 - F, L), (R, L), pcbnew.Edge_Cuts)

    # bottom-left and left edge and top-left corner
    arc(board, (R, L), corner_mid(R, L - R, R, R, L, 0, L - R), (0, L - R),
        pcbnew.Edge_Cuts)
    seg(board, (0, L - R), (0, R), pcbnew.Edge_Cuts)
    arc(board, (0, R), corner_mid(R, R, R, 0, R, R, 0), (R, 0),
        pcbnew.Edge_Cuts)


def hole_positions():
    cx, cy = BOX_W / 2.0, BOX_L / 2.0
    return [(cx + sx * HOLE_PITCH_X / 2.0, cy + sy * HOLE_PITCH_Y / 2.0)
            for sx in (-1, 1) for sy in (-1, 1)]


# ------------------------------------------------------------------- antenna --
def place_antenna(board):
    fp = pcbnew.FootprintLoad(FPLIB, "IFA_2450MHz")
    if fp is None:
        _errors.append("IFA_2450MHz footprint not found")
        return None
    fp.SetReference("AE1")
    fp.SetPosition(pt(*IFA_ORIGIN))
    board.Add(fp)
    for pad in fp.Pads():
        # Pad 1 is the feed; the shorting stub and the arm sit on GND because
        # that is what an IFA is. The net-tie group keeps DRC quiet about it.
        want = "/ANT_FEED" if pad.GetNumber() == "1" else "GND"
        pad.SetNet(ensure_net(board, want))
    return fp


def antenna_copper(board):
    """Board-local bounding boxes of the antenna's copper, pad by pad."""
    fp = board.FindFootprintByReference("AE1")
    if fp is None:
        return []
    out = []
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        out.append((bb.GetLeft() / 1e6 - ORIGIN[0], bb.GetTop() / 1e6 - ORIGIN[1],
                    bb.GetRight() / 1e6 - ORIGIN[0], bb.GetBottom() / 1e6 - ORIGIN[1]))
    return out


# ---------------------------------------------------------------------- main --
def main():
    board = pcbnew.LoadBoard(PCB)

    # Strip everything this script owns. The four ICs currently on the board
    # carry nets from an earlier schematic revision (/+3V3_MCU no longer
    # exists), so they go too - placement re-imports from the netlist.
    # Snapshot every container before removing anything - the SWIG proxies are
    # invalidated by the first Remove().
    stale = (list(board.GetFootprints()) + list(board.GetDrawings())
             + list(board.Zones()) + list(board.GetTracks()))
    for item in stale:
        board.Remove(item)

    draw_outline(board)

    for c in hole_positions():
        circle(board, c, HOLE_DIA, pcbnew.Edge_Cuts)
        circle(board, c, HOLE_KEEPOUT_R * 2, pcbnew.Dwgs_User, width=DOC_W)

    cu = lset(pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

    # Zone A: nothing conductive on any layer except the antenna itself.
    # Tracks and pads are left to the DRU rule, which is the only place that can
    # exempt AE1 - the rule area's own flags have no notion of an exception.
    zone_a = [(0, 0), (BOX_W, 0), (BOX_W, ZONE_A_BOT), (0, ZONE_A_BOT)]
    rule_area(board, "AntennaKeepout", zone_a, cu, tracks=False, pads=False)

    # Zone C: no ground on any layer. The guard pour replaces it.
    zone_c = [(PROBE_X0, ZONE_B_BOT), (PROBE_X1, ZONE_B_BOT),
              (PROBE_X1, TAPER_TOP), ((BOX_W + TIP_W) / 2.0, BOARD_L),
              ((BOX_W - TIP_W) / 2.0, BOARD_L), (PROBE_X0, TAPER_TOP)]
    rule_area(board, "ProbeNoGround", zone_c, lset(pcbnew.In1_Cu),
              tracks=False, vias=False, pads=False, footprints=False)

    # Documentation outlines on the user layers.
    for pts, layer in ((zone_a, pcbnew.User_1), (zone_c, pcbnew.User_2)):
        for i in range(len(pts)):
            seg(board, pts[i], pts[(i + 1) % len(pts)], layer, DOC_W)

    seg(board, (0, ZONE_A_BOT), (BOX_W, ZONE_A_BOT), pcbnew.Dwgs_User, DOC_W)
    text(board, "GND PLANE EDGE - antenna reference", (1.0, ZONE_A_BOT - 0.9),
         pcbnew.Dwgs_User, 0.8)
    seg(board, (PROBE_X0 - 3, SOIL_LINE), (PROBE_X1 + 3, SOIL_LINE),
        pcbnew.Dwgs_User, 0.3)
    text(board, "SOIL LINE", (PROBE_X1 + 4, SOIL_LINE), pcbnew.Dwgs_User, 1.0)
    for y0, y1, nm in ((SENSE2_Y0, SENSE2_Y1, "SENSE2 (air ref)"),
                       (SENSE1_Y0, SENSE1_Y1, "SENSE1 (soil)")):
        for pts in (((PROBE_X0 + 2, y0), (PROBE_X1 - 2, y0)),
                    ((PROBE_X1 - 2, y0), (PROBE_X1 - 2, y1)),
                    ((PROBE_X1 - 2, y1), (PROBE_X0 + 2, y1)),
                    ((PROBE_X0 + 2, y1), (PROBE_X0 + 2, y0))):
            seg(board, pts[0], pts[1], pcbnew.Dwgs_User, DOC_W)
        text(board, nm, (PROBE_X0 + 2.5, (y0 + y1) / 2.0), pcbnew.Dwgs_User, 1.2)

    place_antenna(board)

    # Pours. Ground stops dead at the Zone A boundary and never enters Zone C.
    inset = 0.3
    gnd_b = [(inset, ZONE_A_BOT), (BOX_W - inset, ZONE_A_BOT),
             (BOX_W - inset, ZONE_B_BOT - inset), (inset, ZONE_B_BOT - inset)]
    pour(board, "GND", gnd_b, lset(pcbnew.In1_Cu), "ZoneB_GND")

    guard = [(PROBE_X0 + inset, ZONE_B_BOT - 2.0),
             (PROBE_X1 - inset, ZONE_B_BOT - 2.0),
             (PROBE_X1 - inset, TAPER_TOP - 1.0),
             (PROBE_X0 + inset, TAPER_TOP - 1.0)]
    pour(board, "/SHLD", guard, lset(pcbnew.In2_Cu, pcbnew.B_Cu), "ZoneC_GUARD")

    # ------------------------------------------------------------- self-check
    check(len([d for d in board.GetDrawings()
               if d.GetLayer() == pcbnew.Edge_Cuts]) >= 16,
          "outline: too few Edge.Cuts items")

    for c in hole_positions():
        check(c[0] - HOLE_DIA / 2.0 > 0.5 and c[0] + HOLE_DIA / 2.0 < BOX_W - 0.5,
              f"mounting hole {c} too close to a side edge")
        check(c[1] - HOLE_DIA / 2.0 > 0.5 and c[1] + HOLE_DIA / 2.0 < BOX_L - 0.5,
              f"mounting hole {c} too close to an end edge")

    cu_boxes = antenna_copper(board)
    check(len(cu_boxes) == 3, "antenna footprint missing or wrong pad count")
    for (x0, y0, x1, y1) in cu_boxes:
        check(y0 > 0.3, f"antenna copper only {y0:.2f} mm from the top edge")
        check(y1 <= ZONE_A_BOT + 0.01,
              f"antenna copper reaches y={y1:.2f}, past the Zone A boundary")
        check(x0 > 0.3 and x1 < BOX_W - 0.3,
              f"antenna copper x [{x0:.2f},{x1:.2f}] hits a side edge")
        # Mounting screws are metal and 2.4 GHz does not forgive that.
        for cx, cy in hole_positions():
            clear = HOLE_KEEPOUT_R
            check(cx + clear < x0 or cx - clear > x1
                  or cy + clear < y0 or cy - clear > y1,
                  f"mounting hole ({cx},{cy}) is within {clear} mm of antenna "
                  f"copper [{x0:.2f},{y0:.2f}]-[{x1:.2f},{y1:.2f}]")

    check(SOIL_LINE > ZONE_B_BOT, "soil line is inside the enclosure")
    antenna_to_soil = SOIL_LINE - 3.0
    check(antenna_to_soil >= 50.0,
          f"antenna only {antenna_to_soil:.0f} mm above the soil line")
    check(SENSE2_Y1 < SOIL_LINE, "SENSE2 reference electrode is below the soil line")
    check(SENSE1_Y0 > SOIL_LINE, "SENSE1 electrode is above the soil line")
    check(abs((SENSE2_Y1 - SENSE2_Y0) - (SENSE1_Y1 - SENSE1_Y0)) < 0.01,
          "SENSE1 and SENSE2 electrodes are not the same length")
    check(SENSE1_Y1 <= TAPER_TOP, "SENSE1 electrode runs into the taper")

    if _errors:
        print("ABORT - self-check failed:", file=sys.stderr)
        for e in _errors:
            print("  " + e, file=sys.stderr)
        return 1

    board.BuildListOfNets()
    pcbnew.SaveBoard(PCB, board)

    print(f"board       {BOX_W:.1f} x {BOARD_L:.1f} mm")
    print(f"  zone A    y 0 - {ZONE_A_BOT}      antenna, no copper but the IFA")
    print(f"  zone B    y {ZONE_A_BOT} - {ZONE_B_BOT:.0f}     electronics, "
          f"{BOX_W:.1f} x {ZONE_B_BOT - ZONE_A_BOT:.1f} mm in the 1551WK")
    print(f"  zone C    y {ZONE_B_BOT:.0f} - {BOARD_L:.0f}    probe, {PROBE_W} mm wide")
    print(f"  soil line y {SOIL_LINE:.0f}, antenna {antenna_to_soil:.0f} mm above it, "
          f"insert depth {BOARD_L - SOIL_LINE:.0f} mm")
    print(f"  holes     {HOLE_PITCH_X} x {HOLE_PITCH_Y} mm, "
          + ", ".join(f"({x:.1f},{y:.1f})" for x, y in hole_positions()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
