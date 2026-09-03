#!/usr/bin/env python3
"""Assign the selected parts' 3D models to the board and local footprints.

This is the single source of truth used by both this repair tool and
``tools_gen_pcb.py``.  Reference-specific entries replace models inherited from
system footprints, while footprint-specific entries are also written back to
the local library so an Update Footprints operation cannot lose them.

    $PY tools_3d_models.py            # edit the board AND the .kicad_mod files
    $PY tools_3d_models.py --check    # write the board to /tmp instead

The nPM2100 selection is QEAA: a 4 x 4 mm QFN16.  Do not attach the similarly
named 1.9 mm WLCSP download; Nordic's package table identifies that package as
CAAA.  KiCad's Texas RSA VQFN model matches the selected QFN's 4 x 4 mm body,
0.65 mm pitch, 2.7 mm exposed pad and 0.8 mm minimum package height.

HOW THE ROTATIONS WERE DERIVED, because guessing at this wastes hours
---------------------------------------------------------------------
KiCad's 3D frame is X = footprint X, **Y = MINUS footprint Y**, Z = up out of
the board. So a pad at footprint local (lx, ly) is at 3D (lx, -ly). That sign
is the whole game and it is confirmed by Nordic's model, which is authored for
KiCad: QFN48_6X6_NOR's pin-1 lead sits at model (-2.768, +2.200) and the
footprint's pad 1 is at local (-2.921, -2.200). Same corner, y negated. Both
the QFN48 and the compatible QFN16 model therefore need no rotation.

The two crystal models and the battery-holder model came from vendors with
HEIGHT along +Y instead of +Z - measured with cadquery, not assumed:

    FA-128        x -0.800..0.800 (1.600)  y 0.000..0.500 (0.500)  z -1.000..1.000 (2.000)
    CM8V-T1A      x -1.000..1.000 (2.000)  y 0.000..0.600 (0.600)  z -0.600..0.600 (1.200)
    BU2032 holder x -15.93..15.93 (31.86)  y 0.000..5.200 (5.200) z -9.925..9.925 (19.85)

so they need a -90 degree turn about X to stand them above the component side.
The FA-128 also needs 90 degrees about Z to put its 2.0 mm length along the
footprint's X axis.
"""

import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "moisture-sensor-carrier.kicad_pcb")
LIB = os.path.join(HERE, "lib", "footprints.pretty")

# footprint name -> (model path, offset xyz, rotation xyz)
MODELS_BY_FOOTPRINT = {
    # Nordic's QFN48 model is authored in KiCad's coordinate system and needs
    # no transform.
    "QFN48_6X6_NOR":       ("${KIPRJMOD}/lib/nordic/QFN48_6X6_NOR.step",
                            (0, 0, 0), (0, 0, 0)),

    # Micro Crystal CM8V-T1A, from the vendor bundle in lib/CM8V-T1A/. Height
    # along +Y, 2.0 mm length along X, 1.2 mm along Z. One turn about X stands
    # it up and leaves the length on X, which is where the two pads are
    # (local -0.75 and +0.75). A 2-pin crystal is symmetric, so there is no
    # pin-1 question to get wrong.
    "XTAL_CM8V-T1A_2012":  ("${KIPRJMOD}/lib/CM8V-T1A/"
                            "CM8V-T1A-32.768KHZ-7PF-20PPM-TA-QC.step",
                            (0, 0, 0), (-90, 0, 0)),

    # Epson FA-128. See the long note in the README section below.
    "XTAL_FA-128_2016_4Pin": ("${KIPRJMOD}/lib/FA-128 32.0000MF10Z-AJ0.STEP",
                              (0, 0, 0), (-90, 0, 90)),

    # Both newly supplied models are centred on their land patterns. The
    # inductor is already Z-up; the holder needs its height rotated from +Y.
    "IND_Murata_DFE201210U": (
        "${KIPRJMOD}/lib/DFE201210U_2R2M_P2/IND_DFE201210U-2R2MP2_MUR.step",
        (0, 0, 0), (0, 0, 0)),
    "BatteryHolder_MPD_BU2032SM-BT-GTR": (
        "${KIPRJMOD}/lib/BU2032SM-BT-GTR.STEP",
        (0, 0, 0), (-90, 0, 0)),
}

# The board generator uses reference keys because some selected parts use
# system footprints whose bundled model is absent or inappropriate.
MODELS_BY_REFERENCE = {
    "U1": MODELS_BY_FOOTPRINT["QFN48_6X6_NOR"],
    "U2": (
        "${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/"
        "Texas_RSA_VQFN-16-1EP_4x4mm_P0.65mm_EP2.7x2.7mm.step",
        (0, 0, 0), (0, 0, 0)),
    "U4": ("${KIPRJMOD}/lib/SHT45_AD1F_R2/SHT45-AD1F-R2.step",
           (0, 0, 0), (-90, 0, 0)),
    "X1": MODELS_BY_FOOTPRINT["XTAL_CM8V-T1A_2012"],
    "X2": MODELS_BY_FOOTPRINT["XTAL_FA-128_2016_4Pin"],
    "L10": MODELS_BY_FOOTPRINT["IND_Murata_DFE201210U"],
    "BT1": MODELS_BY_FOOTPRINT["BatteryHolder_MPD_BU2032SM-BT-GTR"],
}


def mm(v):
    return pcbnew.FromMM(v)


def apply_to_board(check):
    board = pcbnew.LoadBoard(BOARD)
    touched = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        name = str(fp.GetFPID().GetLibItemName())
        spec = MODELS_BY_REFERENCE.get(ref, MODELS_BY_FOOTPRINT.get(name))
        if spec is None:
            continue
        path, off, rot = spec
        fp.Models().clear()
        m = pcbnew.FP_3DMODEL()
        m.m_Filename = path
        m.m_Offset = pcbnew.VECTOR3D(*[float(v) for v in off])
        m.m_Rotation = pcbnew.VECTOR3D(*[float(v) for v in rot])
        m.m_Scale = pcbnew.VECTOR3D(1.0, 1.0, 1.0)
        m.m_Show = True
        fp.Models().push_back(m)
        touched += 1
        print(f"  {ref:4s} {name:40s} rot={rot} -> {path}")
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
    for name, (path, off, rot) in MODELS_BY_FOOTPRINT.items():
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
