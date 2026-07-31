#!/usr/bin/env python3
"""
3D model assignment for the project's own footprints.

Four footprints had no model or a misaligned one. The models were all already
on disk - the Nordic ones shipped with the vendor footprint bundle and were
simply never referenced.

    $PY tools_3d_models.py            # edit the board AND the .kicad_mod files
    $PY tools_3d_models.py --check    # write the board to /tmp instead

Both are written, so a re-import from the library stays correct - the same
approach the QFN paste apertures took.

HOW THE ROTATIONS WERE DERIVED, because guessing at this wastes hours
---------------------------------------------------------------------
KiCad's 3D frame is X = footprint X, **Y = MINUS footprint Y**, Z = up out of
the board. So a pad at footprint local (lx, ly) is at 3D (lx, -ly). That sign
is the whole game and it is confirmed by the Nordic models, which are authored
for KiCad: QFN48_6X6_NOR's pin-1 lead sits at model (-2.768, +2.200) and the
footprint's pad 1 is at local (-2.921, -2.200). Same corner, y negated. Both
Nordic models therefore need no rotation at all.

The two crystal models came from vendors and are authored with the package
HEIGHT along +Y instead of +Z - measured with cadquery, not assumed:

    FA-128        x -0.800..0.800 (1.600)  y 0.000..0.500 (0.500)  z -1.000..1.000 (2.000)
    CM8V-T1A      x -1.000..1.000 (2.000)  y 0.000..0.600 (0.600)  z -0.600..0.600 (1.200)

so both need a 90 degree turn about X to stand them up. After that the FA-128
has its 1.6 mm width along X and its 2.0 mm length along Y, which is what its
land pattern wants - see the note on the footprint's F.Fab rectangle below.
"""

import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "moisture-sensor-carrier.kicad_pcb")
LIB = os.path.join(HERE, "lib", "footprints.pretty")

# footprint name -> (model path, offset xyz, rotation xyz)
MODELS = {
    # Nordic's own STEP files, shipped in the same bundle as the footprints and
    # never referenced. Authored for KiCad: pin-1 index solid at model
    # (-2.398, +2.200) for the QFN48 and (-2.002, +1.750) for the QFN32, both
    # over the pin-1 lead, both matching pad 1 once the Y sign is applied.
    "QFN48_6X6_NOR":       ("${KIPRJMOD}/lib/nordic/QFN48_6X6_NOR.step",
                            (0, 0, 0), (0, 0, 0)),
    "QFN32_5X5_NOR":       ("${KIPRJMOD}/lib/nordic/QFN32_5X5_NOR.step",
                            (0, 0, 0), (0, 0, 0)),

    # Micro Crystal CM8V-T1A, from the vendor bundle in lib/CM8V-T1A/. Height
    # along +Y, 2.0 mm length along X, 1.2 mm along Z. One turn about X stands
    # it up and leaves the length on X, which is where the two pads are
    # (local -0.75 and +0.75). A 2-pin crystal is symmetric, so there is no
    # pin-1 question to get wrong.
    "XTAL_CM8V-T1A_2012":  ("${KIPRJMOD}/lib/CM8V-T1A/"
                            "CM8V-T1A-32.768KHZ-7PF-20PPM-TA-QC.step",
                            (0, 0, 0), (90, 0, 0)),

    # Epson FA-128. See the long note in the README section below.
    "XTAL_FA-128_2016_4Pin": ("${KIPRJMOD}/lib/FA-128 32.0000MF10Z-AJ0.STEP",
                              (0, 0, 0), (90, 0, 0)),
}


def mm(v):
    return pcbnew.FromMM(v)


def apply_to_board(check):
    board = pcbnew.LoadBoard(BOARD)
    touched = 0
    for fp in board.GetFootprints():
        name = str(fp.GetFPID().GetLibItemName())
        if name not in MODELS:
            continue
        path, off, rot = MODELS[name]
        fp.Models().clear()
        m = pcbnew.FP_3DMODEL()
        m.m_Filename = path
        m.m_Offset = pcbnew.VECTOR3D(*[float(v) for v in off])
        m.m_Rotation = pcbnew.VECTOR3D(*[float(v) for v in rot])
        m.m_Scale = pcbnew.VECTOR3D(1.0, 1.0, 1.0)
        m.m_Show = True
        fp.Models().push_back(m)
        touched += 1
        print(f"  {fp.GetReference():4s} {name:24s} rot={rot} -> {path}")
    out = "/tmp/models.kicad_pcb" if check else BOARD
    pcbnew.SaveBoard(out, board)
    print(f"{touched} placed footprints updated; wrote {out}")


MODEL_BLOCK = """	(model "{path}"
		(offset
			(xyz {ox} {oy} {oz})
		)
		(scale
			(xyz 1 1 1)
		)
		(rotate
			(xyz {rx} {ry} {rz})
		)
	)
"""


def apply_to_library():
    for name, (path, off, rot) in MODELS.items():
        p = os.path.join(LIB, name + ".kicad_mod")
        if not os.path.exists(p):
            print(f"  (no library file for {name})")
            continue
        s = open(p).read()
        # Drop any existing model block, then append a fresh one before the
        # footprint's closing paren.
        s = re.sub(r"\n\t\(model\b.*?\n\t\)\n", "\n", s, flags=re.S)
        block = MODEL_BLOCK.format(path=path,
                                   ox=off[0], oy=off[1], oz=off[2],
                                   rx=rot[0], ry=rot[1], rz=rot[2])
        i = s.rstrip().rfind(")")
        s = s[:i] + block + s[i:]
        open(p, "w").write(s)
        print(f"  {os.path.basename(p)}")


def main():
    check = "--check" in sys.argv
    apply_to_board(check)
    if not check:
        apply_to_library()


if __name__ == "__main__":
    main()
