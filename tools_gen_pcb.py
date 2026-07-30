#!/usr/bin/env python3
"""Generate the moisture-sensor-carrier board outline, zoning and antenna.

Companion to tools_gen_sch.py. Edit this and re-run; do not hand-edit the
.kicad_pcb. Like the schematic generator it self-checks and aborts rather than
emitting a broken file.

It draws:
  - Edge.Cuts outline (Hammond 1551WK box section + probe stake)
  - four Ø2.6 mounting holes on the 1551WK internal post pattern
  - the three zone boundaries (A antenna / B electronics / C probe)
  - rule areas: AntennaKeepout, ProbeNoGround, NoCopperSHT45
  - the PCB inverted-F antenna, placed as a net-tie footprint
  - In1.Cu GND pour bounded to Zone B, guard pours over Zone C
  - every component from the netlist, placed and netted

The board is rebuilt from scratch each run: it imports the netlist exported
from the schematic, so the two can never drift apart.

Run:  python3 tools_gen_pcb.py
"""
import os
import re
import sys
import math
import subprocess
import pcbnew

# Derive the project root from this file so the generator writes into whichever
# checkout it is run from, not a hardcoded one.
PROJ = os.path.dirname(os.path.abspath(__file__))
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

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
FPLIB_SYS = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
PROJNAME = "moisture-sensor-carrier"

# Solar pre-regulator reserve. Not on the board yet; its output is SOLAR_5V.
SOLAR_RESERVE = (24.0, 49.0, 32.0, 57.0)

# ------------------------------------------------------------- placement ----
# (x, y, rotation[, "B"]).  Board-local mm, rotation CCW as displayed.
#
# Zoning follows LAYOUT.md §4 and §6: RF at the top of Zone B against the
# antenna, nPM1300's SW2 loop at the bottom, FDC1004 near the Zone C boundary
# and as far from both as the board allows.
#
# U1 is rotated 90 deg, which puts its original right edge on top. That lands
# pin 31 (ANT) at the top pointing straight at Zone A, X2 top-left near pins
# 34/35, X1 below near pins 1/2, and the DECD/DECA/DCC cluster on the left.
PLACEMENT = {
    # -- RF matching chain, straight up from U1 pin 31 to the antenna feed.
    # Series L in a column at x=16.8, shunt C alternating either side.
    # C6 sits left, nearest U1 pin 32 (VSS_PA); C9 sits right, where its via
    # down to B.Cu is clear of the chain.
    # The series parts sit on a 1.6 mm pitch, which is the 0201 courtyard plus
    # 0.15 mm. The whole chain has to clear U1's courtyard at y=19.37.
    "L2":  (16.8, 18.5, 90),
    "C6":  (14.9, 18.5, 0),
    "L3":  (16.8, 16.9, 90),
    "C9":  (18.7, 16.9, 0),
    "L4":  (16.8, 15.3, 90),
    "C11": (14.9, 15.3, 0),
    "J5":  (22.6, 13.6, 0),

    # -- MCU and its clocks
    "U1":  (17.0, 23.0, 90),
    # NT1 bridges U1 pin 32 to the centre pad in the 0.1905 mm annulus. Pin 32
    # lands at (16.4, 20.08) after the rotation; its land ends at y=20.460 and
    # pad 49 starts at y=20.650, so the tie sits at the midpoint.
    "NT1": (16.4, 20.555, 0),
    "X2":  (11.0, 20.0, 0),
    "X1":  (11.0, 29.5, 0),

    # -- MCU support, Nordic ref cfg 1. DCC -> L1 -> DECD -> FB1 -> DECA all
    # hug U1's left edge, where those pins land after the rotation.
    "L1":  (10.0, 24.4, 0),
    "C1":  (10.0, 26.3, 0),
    "FB1": (10.0, 22.6, 0),
    "C2":  (6.5, 22.6, 0),
    "C12": (6.5, 24.0, 0),
    "C5":  (6.5, 25.4, 0),
    "C3":  (6.0, 28.2, 0),
    "C4":  (13.3, 17.4, 0),          # pin 36 VDD, top-left
    "C7":  (22.2, 22.0, 90),         # pin 22 VDD, right edge
    "C8":  (20.0, 28.4, 0),          # pin 10 VDD, bottom
    "C10": (10.0, 27.4, 0),          # pins 47/48 VDD, left
    "R1":  (23.0, 18.0, 0),          # RESET filter, pin 30
    "C13": (23.0, 19.6, 0),

    # -- debug and ambient sensor
    "J4":  (11.0, 35.5, 0),          # Tag-Connect, zero height
    "U4":  (30.0, 34.5, 0),          # SHT45 - needs a lid vent above it
    "C27": (30.0, 37.5, 0),
    "R22": (24.5, 33.5, 0),          # I2C pull-ups on always-on +3V3
    "R23": (24.5, 35.0, 0),

    # -- USB-C on the left edge. The HRO footprint mates toward +Y, so 270 deg
    # points the opening at -X. Origin at x=3.5 puts the body face 0.2 mm proud
    # of the board edge, which keeps the plug overmold off the FR4.
    "J1":  (3.5, 45.5, 270),

    # -- solar input, right side, next to the 8x8 pre-regulator reserve
    "J3":  (28.5, 44.5, 0),
    "D5":  (23.0, 41.5, 90),
    "TP5": (21.5, 49.5, 0),

    # -- PMIC and the switching loop, bottom of Zone B and away from sense
    "U2":  (9.5, 56.0, 0),
    "L10": (4.0, 53.5, 0),           # SW2 -> L10 -> C24, kept tiny
    "C24": (4.0, 57.0, 0),
    "C21": (15.0, 51.5, 0),
    "C22": (15.0, 54.0, 0),
    "C20": (15.0, 56.5, 0),
    "C23": (15.0, 59.0, 0),
    "C25": (12.5, 61.5, 0),
    "C26": (17.0, 63.0, 0),
    "R20": (5.5, 60.0, 0),
    "R21": (8.5, 60.0, 0),

    # -- battery, thermistor, charge LEDs. J2 sits left of the lower-right
    # mounting screw, which blocks x 26.5-32.5 between y 61.5 and 67.5.
    "J2":  (20.8, 69.0, 0),
    "TH1": (21.5, 57.5, 0),
    "D3":  (30.0, 68.5, 0),
    "D4":  (30.0, 71.0, 0),
    "R25": (26.5, 68.5, 0),
    "R26": (26.5, 71.0, 0),

    # -- sense front end, hard against the Zone C boundary
    "U3":  (11.0, 68.5, 0),
    "TP1": (9.0, 72.5, 0),           # SENSE1
    "TP2": (12.0, 72.5, 0),          # SENSE2
    "TP3": (15.0, 72.5, 0),          # SHLD
    "TP4": (19.0, 49.5, 0),          # SHPHLD, at the PMIC
    "NT2": (19.8, 15.2, 0, "B"),     # C9 ground tie, B.Cu, under C9's via
}

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
_notes = []


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


# ------------------------------------------------------------------ netlist --
def netlist():
    """Export and parse the schematic netlist. Components and pad nets both come
    from here so the board can never drift from the schematic."""
    out = f"{PROJ}/.netlist.tmp.net"
    r = subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--output", out,
                        f"{PROJ}/{PROJNAME}.kicad_sch"],
                       capture_output=True, text=True)
    if not os.path.exists(out):
        raise SystemExit(f"ABORT: netlist export failed\n{r.stderr}")
    s = open(out).read()
    os.remove(out)
    comps = {}
    for ref, body in re.findall(
            r'\(comp\s+\(ref "([^"]+)"\)(.*?)\n\t\t\)\n', s, re.S):
        v = re.search(r'\(value "([^"]*)"', body)
        f = re.search(r'\(footprint "([^"]+)"', body)
        if not f:
            raise SystemExit(f"ABORT: {ref} has no footprint")
        comps[ref] = (v.group(1) if v else "", f.group(1))
    pads = {}
    for name, body in re.findall(
            r'\(net\s+\(code "\d+"\)\s+\(name "([^"]+)"\)(.*?)\n\t\t\)\n', s, re.S):
        for ref, pin in re.findall(r'\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', body):
            pads[(ref, pin)] = name
    return comps, pads


def load_fp(board, fpid, ref, value):
    lib, name = fpid.split(":", 1)
    path = FPLIB if lib == "footprints" else f"{FPLIB_SYS}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit(f"ABORT: footprint {fpid} not found for {ref}")
    fp.SetReference(ref)
    fp.SetValue(value)
    dedupe_text(fp, ref)
    return fp


def dedupe_text(fp, ref):
    """Both Nordic QFN footprints carry their pin-1 '*' marker twice, at
    identical coordinates on identical layers - once in the old unquoted-layer
    block and once again in the converted one. It prints on top of itself and
    every DRC run reports a silkscreen overlap. Strip the duplicates here rather
    than editing the vendor files, so their provenance stays intact."""
    seen, dupes = set(), []
    for g in fp.GraphicalItems():
        if not isinstance(g, pcbnew.PCB_TEXT):
            continue
        key = (g.GetLayer(), g.GetText(),
               round(g.GetPosition().x, 3), round(g.GetPosition().y, 3))
        if key in seen:
            dupes.append(g)
        else:
            seen.add(key)
    for g in dupes:
        fp.Remove(g)
    if dupes:
        _notes.append(f"{ref}: removed {len(dupes)} duplicated text item(s) "
                      f"from the vendor footprint")
    return fp


def place_components(board, comps, pads):
    placed = {}
    for ref, (value, fpid) in sorted(comps.items()):
        if ref not in PLACEMENT:
            _errors.append(f"{ref} ({fpid}) has no entry in PLACEMENT")
            continue
        x, y, rot = PLACEMENT[ref][:3]
        back = len(PLACEMENT[ref]) > 3 and PLACEMENT[ref][3] == "B"
        fp = load_fp(board, fpid, ref, value)
        attach_model(fp, ref)
        board.Add(fp)
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        if back:
            fp.Flip(pt(x, y), False)
        for pad in fp.Pads():
            n = pads.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(ensure_net(board, n))
        # Reference text on the fab layer only; silk is too crowded at this size.
        fp.Reference().SetLayer(pcbnew.F_Fab if not back else pcbnew.B_Fab)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.5), mm(0.5)))
        fp.Reference().SetTextThickness(mm(0.08))
        # Values duplicate the BOM and are what makes the silk unreadable at
        # this density. Keep them on Fab, hidden.
        fp.Value().SetLayer(pcbnew.F_Fab if not back else pcbnew.B_Fab)
        fp.Value().SetVisible(False)
        if ref in EDGE_PARTS:
            # An edge connector's body overhangs, so its silk outline runs off
            # the board and gets clipped by the router. Move it to Fab.
            for g in fp.GraphicalItems():
                if g.GetLayer() == pcbnew.F_SilkS:
                    g.SetLayer(pcbnew.F_Fab)
        placed[ref] = fp
    return placed


def courtyard(fp):
    """Board-local (x0, y0, x1, y1) of a footprint's courtyard, falling back to
    its pad extent when it has none (net ties)."""
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            b = g.GetBoundingBox()
            xs += [b.GetLeft(), b.GetRight()]
            ys += [b.GetTop(), b.GetBottom()]
    if not xs:
        for p in fp.Pads():
            b = p.GetBoundingBox()
            xs += [b.GetLeft(), b.GetRight()]
            ys += [b.GetTop(), b.GetBottom()]
    if not xs:
        return None
    return (min(xs) / 1e6 - ORIGIN[0], min(ys) / 1e6 - ORIGIN[1],
            max(xs) / 1e6 - ORIGIN[0], max(ys) / 1e6 - ORIGIN[1])


def overlaps(a, b, gap=0.0):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0]
                or a[3] + gap <= b[1] or b[3] + gap <= a[1])


# 3D models the footprint does not carry itself, keyed by reference.
# (path, (dx, dy, dz) mm, (rx, ry, rz) deg).
#
# Nordic ship STEP for both QFN packages but their KiCad-converted footprints
# reference nothing. Both files are centred on origin with Z running 0 to 0.892
# up from the board, which is exactly KiCad's convention, so they need no
# offset or rotation. Verified by extracting the STEP bounding boxes:
#   QFN48  x,y +/-2.997  z 0..0.892   (package is 6.0 x 6.0 x 0.85 nom)
#   QFN32  x,y +/-2.502  z 0..0.892   (package is 5.0 x 5.0 x 0.85 nom)
#
# The three vendor models added by hand are all Y-up CAD exports - their height
# runs along Y, not Z - so each carries a -90 deg rotation about X. Confirmed by
# extracting their bounding boxes:
#   CM8V-T1A   x 2.000 (length ok)   z 1.200 (the 1.2 mm width)   y = height
#   SHT45      x 1.502, z 1.502 (the 1.5 x 1.5 body)              y = height
#   1551WK     x 80.00 (box length)  z 40.00 (box width)          y = height
# These rotations are a best guess from the bounding boxes and want eyeballing
# in the 3D viewer before anyone trusts a clearance measured off them.
MODELS_3D = {
    "U1": ("${KIPRJMOD}/lib/nordic/QFN48_6X6_NOR.step", (0, 0, 0), (0, 0, 0)),
    "U2": ("${KIPRJMOD}/lib/nordic/QFN32_5X5_NOR.step", (0, 0, 0), (0, 0, 0)),
    "J1": ("${KIPRJMOD}/lib/TYPE-C-31-M-12--3DModel-STEP-56544.STEP",
           (0, 0, 0), (0, 0, 0)),
    "U4": ("${KIPRJMOD}/lib/SHT45_AD1F_R2/SHT45-AD1F-R2.step",
           (0, 0, 0), (-90, 0, 0)),
    "X1": ("${KIPRJMOD}/lib/CM8V-T1A/CM8V-T1A-32.768KHZ-7PF-20PPM-TA-QC.step",
           (0, 0, 0), (-90, 0, 0)),
}

# Mechanical-only footprints: no pads, no netlist entry, 3D model only. Placed
# so the enclosure fit can be checked in the 3D viewer instead of on paper.
# The board sits on the 4.00 mm posts, so its top face is 5.60 mm above the box
# floor; the model is dropped by that much and centred on the box section.
# Set False to leave the enclosure out entirely. The footprint also carries no
# smd/through_hole attribute, so KiCad's 3D viewer files it under "Other" and it
# can be switched off on its own in Preferences > Display Options.
SHOW_ENCLOSURE = True

# Hammond's STEP is Y-up and its screw side faces the board, so it needs
# flipping: +90 about X rather than -90. ENCL_Z then drops it so the box
# interior floor sits 5.60 mm below the board top face (4.00 mm posts + 1.6 mm
# board). Tune these two if the fit looks wrong in the viewer.
ENCL_ROT = (90, 0, 90)
ENCL_Z = 14.7

DECOR = {
    "MP1": ("Enclosure_1551WK", (BOX_W / 2.0, BOX_L / 2.0), 0,
            "${KIPRJMOD}/lib/enclosure/1551WKBK.stp", (0, 0, ENCL_Z), ENCL_ROT),
} if SHOW_ENCLOSURE else {}

# References that legitimately have no 3D model: bare copper, or no part fitted.
NO_MODEL_EXPECTED = {"AE1", "NT1", "NT2", "J4", "J5",
                     "TP1", "TP2", "TP3", "TP4", "TP5"}

# Mechanical-only footprints are not in the netlist, so the placement checks
# must skip them.
DECOR_REFS = {"MP1"}


def attach_model(fp, ref, spec=None):
    if spec is None:
        if ref not in MODELS_3D:
            return
        spec = MODELS_3D[ref]
    path, off, rot = spec
    # Drop whatever the footprint shipped with. For J1 and U4 that is a KiCad
    # path pointing at a .step this install does not have, and leaving it in
    # place would stack a broken reference on top of the working one.
    fp.Models().clear()
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = path
    m.m_Offset = pcbnew.VECTOR3D(*[float(v) for v in off])
    m.m_Rotation = pcbnew.VECTOR3D(*[float(v) for v in rot])
    m.m_Scale = pcbnew.VECTOR3D(1.0, 1.0, 1.0)
    m.m_Show = True
    fp.Models().push_back(m)


# Connectors that mate through the board edge. Their bodies overhang on purpose,
# so the courtyard check is relaxed and only their pads have to land on copper.
EDGE_PARTS = {"J1"}


def inside_board(box, ref=None):
    """Every corner of box must sit inside the outline with edge clearance."""
    x0, y0, x1, y1 = box
    m = 0.0 if ref in EDGE_PARTS else 0.3
    if y1 <= ZONE_B_BOT:                       # box section
        return (x0 >= -m - (2.0 if ref in EDGE_PARTS else 0.0)
                and x1 <= BOX_W - m and y0 >= m and y1 <= BOX_L)
    if y0 >= ZONE_B_BOT:                       # probe
        return (x0 >= PROBE_X0 + m and x1 <= PROBE_X1 - m and y1 <= TAPER_TOP)
    return False                               # straddles the shoulder


def pad_extent(fp):
    xs, ys = [], []
    for p in fp.Pads():
        b = p.GetBoundingBox()
        xs += [b.GetLeft(), b.GetRight()]
        ys += [b.GetTop(), b.GetBottom()]
    return (min(xs) / 1e6 - ORIGIN[0], min(ys) / 1e6 - ORIGIN[1],
            max(xs) / 1e6 - ORIGIN[0], max(ys) / 1e6 - ORIGIN[1])


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

    comps, pads = netlist()
    fps = place_components(board, comps, pads)

    for ref, (fpname, at, rot, path, off, mrot) in DECOR.items():
        d = pcbnew.FootprintLoad(FPLIB, fpname)
        if d is None:
            _errors.append(f"decor footprint {fpname} not found")
            continue
        d.SetReference(ref)
        attach_model(d, ref, (path, off, mrot))
        board.Add(d)
        d.SetPosition(pt(*at))
        d.SetOrientationDegrees(rot)

    # No copper under the SHT45 except its four pin pads (datasheet §5.3).
    if "U4" in fps:
        c = courtyard(fps["U4"])
        pad = 0.4
        box = [(c[0] - pad, c[1] - pad), (c[2] + pad, c[1] - pad),
               (c[2] + pad, c[3] + pad), (c[0] - pad, c[3] + pad)]
        rule_area(board, "NoCopperSHT45", box, cu,
                  tracks=True, vias=True, pads=False, fills=True, footprints=False)
        for i in range(4):
            seg(board, box[i], box[(i + 1) % 4], pcbnew.User_3, DOC_W)

    # Solar pre-regulator reserve, documentation only.
    sx0, sy0, sx1, sy1 = SOLAR_RESERVE
    for a, b in (((sx0, sy0), (sx1, sy0)), ((sx1, sy0), (sx1, sy1)),
                 ((sx1, sy1), (sx0, sy1)), ((sx0, sy1), (sx0, sy0))):
        seg(board, a, b, pcbnew.Dwgs_User, DOC_W)
    text(board, "SOLAR PRE-REG 8x8 RESERVE", (sx0 + 0.3, sy0 + 1.2),
         pcbnew.Dwgs_User, 0.7)

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

    # Probe electrodes on F.Cu, with the guard filling around them. LAYOUT.md §5
    # wants guard on both sides of every sense feature at a 0.2 mm gap - that is
    # a minimum-clearance rule, not a keep-away, so the coupling is deliberate.
    # SENSE1 and SENSE2 are identical 16 x 30 mm so the ratio cancels drift.
    ex0, ex1 = PROBE_X0 + 2.0, PROBE_X1 - 2.0
    for net, y0, y1, nm in (("/SENSE2", SENSE2_Y0, SENSE2_Y1, "SENSE2_electrode"),
                            ("/SENSE1", SENSE1_Y0, SENSE1_Y1, "SENSE1_electrode")):
        z = pour(board, net, [(ex0, y0), (ex1, y0), (ex1, y1), (ex0, y1)],
                 lset(pcbnew.F_Cu), nm)
        if z:
            z.SetAssignedPriority(2)
            z.SetLocalClearance(mm(0.2))
    zg = pour(board, "/SHLD", guard, lset(pcbnew.F_Cu), "ZoneC_GUARD_F")
    if zg:
        zg.SetAssignedPriority(1)
        zg.SetLocalClearance(mm(0.2))

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

    # ---- placement -----------------------------------------------------------
    for ref in PLACEMENT:
        check(ref in comps, f"PLACEMENT has {ref}, which is not in the netlist")

    boxes = {r: courtyard(f) for r, f in fps.items()}
    boxes = {r: b for r, b in boxes.items() if b}
    order = sorted(boxes)
    for i, a in enumerate(order):
        for b in order[i + 1:]:
            # NT1 lives under U1's centre pad on purpose; that is the rule, not
            # a collision.
            if {a, b} == {"NT1", "U1"}:
                continue
            if fps[a].IsFlipped() != fps[b].IsFlipped():
                continue
            if overlaps(boxes[a], boxes[b]):
                _errors.append(f"courtyard overlap: {a} and {b}")

    for r, b in boxes.items():
        check(inside_board(b, r), f"{r} courtyard {[round(v, 2) for v in b]} "
                                  f"is outside the outline or too close to an edge")
        if r in EDGE_PARTS:
            # The body may overhang; every pad still has to land on the board.
            pb = pad_extent(fps[r])
            check(pb[0] >= 0.3 and pb[2] <= BOX_W - 0.3
                  and pb[1] >= 0.3 and pb[3] <= BOX_L - 0.3,
                  f"{r} has pads off the board: {[round(v, 2) for v in pb]}")
        if r != "AE1":
            check(b[1] >= ZONE_A_BOT,
                  f"{r} is inside the antenna keepout (Zone A)")
        for cx, cy in hole_positions():
            check(not overlaps(b, (cx - HOLE_KEEPOUT_R, cy - HOLE_KEEPOUT_R,
                                   cx + HOLE_KEEPOUT_R, cy + HOLE_KEEPOUT_R)),
                  f"{r} fouls the mounting screw at ({cx},{cy})")

    # The two grounding rules that the DRU cannot express (LAYOUT.md §2).
    if "NT1" in fps and "U1" in fps:
        check(not fps["NT1"].IsFlipped(), "NT1 must be on F.Cu")

        def padbox(fp, num):
            for p in fp.Pads():
                if p.GetNumber() == num:
                    b = p.GetBoundingBox()
                    return (b.GetLeft() / 1e6, b.GetTop() / 1e6,
                            b.GetRight() / 1e6, b.GetBottom() / 1e6)
            return None

        # The tie is only doing its job if pad 1 actually lands on the pin-32
        # copper and pad 2 on the centre pad. Anything else and GND_PA reaches
        # ground somewhere Nordic did not intend.
        for tie_pad, u1_pad, what in (("1", "32", "the pin-32 land"),
                                      ("2", "49", "the centre pad")):
            a, b = padbox(fps["NT1"], tie_pad), padbox(fps["U1"], u1_pad)
            check(a and b and overlaps(a, b),
                  f"NT1 pad {tie_pad} does not overlap U1 pad {u1_pad} ({what})")
    if "NT2" in fps:
        check(fps["NT2"].IsFlipped(), "NT2 must be on B.Cu")

    # LAYOUT.md §6 / the DRU: keep the measurement away from the switchers.
    # Component-level proxy for the track rule, which cannot fire before routing.
    for sense in ("U3", "TP1", "TP2"):
        for switcher in ("L10", "C24", "U2"):
            if sense in boxes and switcher in boxes:
                a, b = boxes[sense], boxes[switcher]
                d = math.hypot(max(0, max(a[0] - b[2], b[0] - a[2])),
                               max(0, max(a[1] - b[3], b[1] - a[3])))
                check(d >= 3.0,
                      f"{sense} is {d:.1f} mm from {switcher}, under the 3 mm "
                      f"SENSE-to-SWITCH rule")

    # ---- 3D coverage ---------------------------------------------------------
    # Reported, not fatal: a missing model does not affect the netlist or the
    # copper, but it does mean the enclosure fit cannot be checked in 3D.
    ki3d = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels"
    no_ref, broken = [], []
    for ref, fp in sorted(fps.items()):
        models = list(fp.Models())
        if not models:
            if ref not in NO_MODEL_EXPECTED:
                no_ref.append(ref)
            continue
        for m in models:
            p = str(m.m_Filename)
            for var in ("KICAD10_3DMODEL_DIR", "KICAD9_3DMODEL_DIR",
                        "KICAD8_3DMODEL_DIR"):
                p = p.replace("${%s}" % var, ki3d)
            p = p.replace("${KIPRJMOD}", PROJ)
            if not any(os.path.exists(os.path.splitext(p)[0] + e)
                       for e in (os.path.splitext(p)[1], ".step", ".stp", ".wrl")):
                broken.append((ref, str(m.m_Filename)))
    if no_ref:
        _notes.append(f"3D: no model referenced for {', '.join(no_ref)}")
    for ref, p in broken:
        _notes.append(f"3D: {ref} references a file that is not on disk - "
                      f"{os.path.basename(p)}")

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
    # Fill the pours so the electrodes and planes are real copper the DRC can
    # see. Routing will invalidate them; re-running this script refills.
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
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
    area = sum((b[2] - b[0]) * (b[3] - b[1]) for b in boxes.values())
    zb = BOX_W * (ZONE_B_BOT - ZONE_A_BOT)
    for n in _notes:
        print(f"  note      {n}")
    print(f"  placed    {len(fps)} components, {area:.0f} mm2 of courtyard "
          f"in {zb:.0f} mm2 of Zone B ({100 * area / zb:.0f} %)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
