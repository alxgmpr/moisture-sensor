#!/usr/bin/env python3
"""
Generate the GND stitching via list for tools_route.py.

ZoneB_GND_F on F.Cu collects the ground pads; these vias tie that pour through
to the In1.Cu plane. A 2.5 mm grid, then everything that collides is dropped:
pads, footprint bodies, existing tracks and vias, and four banned regions.

    $PY tools_stitch_gen.py          # prints the list; paste it into STITCH

Run it AFTER routing, not before - it reads the tracks that are on the board
and keeps out of their way, so re-running it before the routes exist would
propose vias on top of them. GND vias are ignored as obstacles, since those
are the output of a previous run; everything else is respected.
"""

import os

import pcbnew

BOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "moisture-sensor-carrier.kicad_pcb")

PITCH = 2.5
VIA_R = 0.30                 # 0.6 mm via
KEEP_PAD = 0.35              # beyond the annulus, to pads and bodies
KEEP_TRK = 0.45              # beyond the annulus, to existing copper

# Where a stitching via is banned outright, whatever the geometry says.
BANNED = [
    (73.40,  51.00,  81.30,  61.20, "RF corridor - no plane perforation "
                                    "under the microstrip or its return"),
    (65.50, 104.50,  78.00, 115.00, "sense escape - In1.Cu is carved away here"),
    (93.50,  40.00, 103.00, 195.00, "SHT45 jut-out - SHT45_Jut bans vias"),
    (60.00,  40.00, 103.00,  53.40, "Zone A - above the F.Cu pour"),
    (60.00, 103.60, 103.00, 195.00, "below the F.Cu pour"),
]


def main():
    bd = pcbnew.LoadBoard(BOARD)
    mm = pcbnew.ToMM

    boxes = []
    for fp in bd.GetFootprints():
        if fp.GetReference() == "MP1":       # the enclosure, not a part
            continue
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            boxes.append((mm(bb.GetLeft()), mm(bb.GetTop()),
                          mm(bb.GetRight()), mm(bb.GetBottom())))
        bb = fp.GetBoundingBox(False, False)
        boxes.append((mm(bb.GetLeft()), mm(bb.GetTop()),
                      mm(bb.GetRight()), mm(bb.GetBottom())))

    segs, vias = [], []
    for t in bd.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            # Skip GND vias: those are the stitching this script generates, so
            # counting them as obstacles makes a second run return nothing.
            if t.GetNetname() == "GND":
                continue
            p = t.GetPosition()
            vias.append((mm(p.x), mm(p.y)))
        else:
            a, b = t.GetStart(), t.GetEnd()
            segs.append((mm(a.x), mm(a.y), mm(b.x), mm(b.y)))

    def near_seg(x, y, s, r):
        ax, ay, bx, by = s
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        cx, cy = ax + t * dx, ay + t * dy
        return (x - cx) ** 2 + (y - cy) ** 2 < r * r

    def blocked(x, y):
        for x1, y1, x2, y2, _ in BANNED:
            if x1 < x < x2 and y1 < y < y2:
                return True
        r = VIA_R + KEEP_PAD
        for x1, y1, x2, y2 in boxes:
            if x1 - r < x < x2 + r and y1 - r < y < y2 + r:
                return True
        r = VIA_R + KEEP_TRK
        for vx, vy in vias:
            if (x - vx) ** 2 + (y - vy) ** 2 < (r + VIA_R) ** 2:
                return True
        for s in segs:
            if near_seg(x, y, s, r):
                return True
        return False

    out = []
    y = 55.0
    while y <= 103.0:
        x = 61.5
        while x <= 92.5:
            if not blocked(x, y):
                out.append((round(x, 2), round(y, 2)))
            x += PITCH
        y += PITCH

    print(f"# {len(out)} stitching vias, {PITCH} mm grid")
    for i in range(0, len(out), 4):
        print("    " + " ".join(f"({a:6.2f}, {b:6.2f})," for a, b in out[i:i + 4]))


if __name__ == "__main__":
    main()
