#!/usr/bin/env python3
"""
Footprint corrections, applied to BOTH the library .kicad_mod and the placed
instance on the board, so a re-import from the library stays correct.

    $PY tools_fix_footprints.py            # edit the board and the library
    $PY tools_fix_footprints.py --check    # write the board to /tmp instead

Idempotent: pads are renamed by their position in the footprint, not by their
current name, so a second run is a no-op.

X2 / XTAL_FA-128_2016_4Pin - THE PAD NUMBERING WAS ON THE WRONG DIAGONAL
------------------------------------------------------------------------
Found by trying to line up the 3D model's pin-1 index with the footprint's.
The model was right and the footprint was wrong.

From the FA-128 datasheet, page 1, "External dimensions" TOP VIEW with the
2.0 mm axis horizontal:

        #4  +-----------+  #3
            |           |
        #1  +-----------+  #2

and the "Internal connection (TOP VIEW)" inset puts the resonator between
**#1 and #3**, with the note "#2 and #4 are connected to the cover. (Please
connect to ground)". So the crystal terminals are the BL-TR diagonal and the
cover pads are the BR-TL diagonal.

Epson's recommended land, same page, is **1.45 mm wide x 2.00 mm tall**
(0.95 mm x-centres, 1.15 mm y-centres, 0.5 x 0.85 mm pads) - the part sits
with its 2.0 mm axis VERTICAL. Our footprint copies that land exactly, so the
part is rotated 90 degrees from the dimension drawing. Rotating the pinout
with it, either way round:

    90 CW   #1 TL  #2 BL  #3 BR  #4 TR      crystal on TL-BR
    90 CCW  #1 BR  #2 TR  #3 TL  #4 BL      crystal on TL-BR

Both give the same answer, because 180 degrees maps a diagonal to itself:
**with the 2.0 mm axis vertical the crystal terminals are always TL-BR.**

The footprint had pad 1 at BL and pad 3 at TR - the COVER diagonal. The
schematic wires pad 1 to XC1 and pad 3 to XC2, so XC1 and XC2 would have
landed on the two cover pads while the actual crystal terminals were tied to
GND through pads 2 and 4. The 32 MHz oscillator would not have started, and
nothing in ERC or DRC can see it: all four pads exist, all four are connected,
and the two ground pads are legitimately ground.

Fixed by rotating the numbering one position, which keeps 1-3 and 2-4 diagonal
as the part requires and puts pad 1 on the TL corner where the model's lid
index sits. The silkscreen pin-1 dot moves to match, and the F.Fab rectangle -
which was drawn 2.0 wide x 1.6 tall, transposed relative to its own pads - is
corrected to 1.6 x 2.0 with its chamfer on the new pin-1 corner.
"""

import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "nrf-moisture-sensor.kicad_pcb")
LIB = os.path.join(HERE, "lib", "footprints.pretty")

# footprint -> {(local x, local y): pad name}
RENUMBER = {
    "XTAL_FA-128_2016_4Pin": {
        (-0.475, -0.575): "1",   # TL - crystal terminal, index corner
        (-0.475,  0.575): "2",   # BL - cover / GND
        ( 0.475,  0.575): "3",   # BR - crystal terminal
        ( 0.475, -0.575): "4",   # TR - cover / GND
    },
}

# footprint -> list of (kind, old geometry, new geometry) for the graphics
GRAPHICS = {
    "XTAL_FA-128_2016_4Pin": [
        # silk pin-1 dot: beside pad 1, which is now the TOP-left corner
        ("circle", (-1.45,  0.575), (-1.45, -0.575)),
        # F.Fab body outline was transposed: 2.0 x 1.6 where the pads say
        # 1.6 x 2.0. Redrawn, with the pin-1 chamfer on the TL corner.
        ("rect",   ((-1.0, -0.8), (1.0, 0.8)), ((-0.8, -1.0), (0.8, 1.0))),
        ("line",   ((-1.0, -0.35), (-0.55, -0.8)), ((-0.8, -0.55), (-0.55, -1.0))),
    ],
}

# footprint -> {pad name: net name}. The schematic binds nets to pad NUMBERS,
# so a renumbering has to carry the net with the number and not with the piece
# of copper. Stated explicitly rather than captured before the rename, so the
# script stays idempotent and so this file says out loud what the schematic
# says: tools_gen_sch.py wires X2 pin 1 to XC1, pin 3 to XC2, pins 2 and 4 to
# GND. If that ever changes, change it here too.
NETS = {
    "XTAL_FA-128_2016_4Pin": {"1": "/XC1", "2": "GND", "3": "/XC2", "4": "GND"},
}

TOL = 0.005


def close(a, b):
    return abs(a - b) < TOL


def apply_to_board(check):
    board = pcbnew.LoadBoard(BOARD)
    for fp in board.GetFootprints():
        name = str(fp.GetFPID().GetLibItemName())
        if name not in RENUMBER:
            continue
        c = fp.GetPosition()
        print(f"  {fp.GetReference()} ({name})")

        for pad in fp.Pads():
            p = pad.GetPosition()
            lx = pcbnew.ToMM(p.x - c.x)
            ly = pcbnew.ToMM(p.y - c.y)
            for (tx, ty), new in RENUMBER[name].items():
                if close(lx, tx) and close(ly, ty):
                    old = pad.GetPadName()
                    if old != new:
                        pad.SetPadName(new)
                        print(f"    pad at ({lx:+.3f},{ly:+.3f}) {old} -> {new}")
                    break
            else:
                raise SystemExit(f"unmatched pad at ({lx:+.3f},{ly:+.3f})")

        for pad in fp.Pads():
            want = NETS[name][pad.GetPadName()]
            if pad.GetNetname() != want:
                ni = board.FindNet(want)
                if ni is None or not hasattr(ni, "GetNetCode"):
                    raise SystemExit(f"net lookup failed for {want!r}")
                was = pad.GetNetname()
                pad.SetNetCode(ni.GetNetCode())
                print(f"    pad {pad.GetPadName()} net {was} -> {want}")

        for kind, old, new in GRAPHICS.get(name, []):
            for g in fp.GraphicalItems():
                if not isinstance(g, pcbnew.PCB_SHAPE):
                    continue
                s, e = g.GetStart(), g.GetEnd()
                lsx, lsy = pcbnew.ToMM(s.x - c.x), pcbnew.ToMM(s.y - c.y)
                lex, ley = pcbnew.ToMM(e.x - c.x), pcbnew.ToMM(e.y - c.y)
                if kind == "circle" and close(lsx, old[0]) and close(lsy, old[1]):
                    d = pcbnew.ToMM(e.x - s.x)          # keep the radius
                    g.SetStart(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(new[0]),
                                               c.y + pcbnew.FromMM(new[1])))
                    g.SetEnd(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(new[0] + d),
                                             c.y + pcbnew.FromMM(new[1])))
                    print(f"    silk dot {old} -> {new}")
                elif kind in ("rect", "line") and \
                        close(lsx, old[0][0]) and close(lsy, old[0][1]) and \
                        close(lex, old[1][0]) and close(ley, old[1][1]):
                    g.SetStart(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(new[0][0]),
                                               c.y + pcbnew.FromMM(new[0][1])))
                    g.SetEnd(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(new[1][0]),
                                             c.y + pcbnew.FromMM(new[1][1])))
                    print(f"    {kind} {old} -> {new}")

    out = "/tmp/fixed.kicad_pcb" if check else BOARD
    pcbnew.SaveBoard(out, board)
    print(f"wrote {out}")


def apply_to_library():
    for name, pads in RENUMBER.items():
        p = os.path.join(LIB, name + ".kicad_mod")
        s = open(p).read()

        def pad_sub(m):
            x, y = float(m.group(2)), float(m.group(3))
            for (tx, ty), new in pads.items():
                if close(x, tx) and close(y, ty):
                    return f'(pad "{new}"{m.group(4)}(at {m.group(2)} {m.group(3)})'
            raise SystemExit(f"unmatched library pad at ({x},{y})")

        s = re.sub(r'\(pad "(\d)"(\s+smd\s+\w+\s+)\(at ([-0-9.]+) ([-0-9.]+)\)',
                   lambda m: f'(pad "{_name(pads, m.group(3), m.group(4))}"'
                             f'{m.group(2)}(at {m.group(3)} {m.group(4)})', s)

        for old, new in (
            ("(fp_circle (center -1.45 0.575) (end -1.35 0.575)",
             "(fp_circle (center -1.45 -0.575) (end -1.35 -0.575)"),
            ("(fp_rect (start -1.0 -0.8) (end 1.0 0.8)",
             "(fp_rect (start -0.8 -1.0) (end 0.8 1.0)"),
            ("(fp_line (start -1.0 -0.35) (end -0.55 -0.8)",
             "(fp_line (start -0.8 -0.55) (end -0.55 -1.0)"),
            ("Pads 1 and 3 are the crystal terminals; pads 2 and 4 are the metal cover and must go to ground.",
             "Pads 1 and 3 are the crystal terminals; pads 2 and 4 are the metal cover and must go to ground. "
             "PAD NUMBERING CORRECTED: pad 1 is the TOP-LEFT corner. Epson's dimension drawing puts the resonator "
             "between #1 and #3 with the 2.0 mm axis horizontal, and their recommended land is 1.45 x 2.00, i.e. "
             "the part sits with its 2.0 mm axis VERTICAL - so the crystal terminals fall on the TL-BR diagonal. "
             "This footprint previously had 1 and 3 on BL-TR, the COVER diagonal, which would have put XC1/XC2 on "
             "the grounded cover and shorted the crystal to GND."),
        ):
            if old not in s:
                print(f"    (library already patched: {old[:40]}...)")
            s = s.replace(old, new)

        open(p, "w").write(s)
        print(f"  {os.path.basename(p)}")


def _name(pads, xs, ys):
    x, y = float(xs), float(ys)
    for (tx, ty), new in pads.items():
        if close(x, tx) and close(y, ty):
            return new
    raise SystemExit(f"unmatched library pad at ({x},{y})")


def main():
    check = "--check" in sys.argv
    apply_to_board(check)
    if not check:
        apply_to_library()


if __name__ == "__main__":
    main()
