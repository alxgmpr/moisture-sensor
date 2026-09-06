#!/usr/bin/env python3
"""Apply procurement-driven footprint changes to the placed PCB.

Replaces only C30 and TH1, retaining placement, orientation and pad-number net
assignments. Use --check to write /tmp/moisture-bom-footprints.kicad_pcb.
"""

import os
import re
import sys
import tempfile

import pcbnew


HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_PATH = os.path.join(HERE, "nrf-moisture-sensor.kicad_pcb")
KICAD_FP = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

REPLACEMENTS = {
    "C30": (
        os.path.join(KICAD_FP, "Capacitor_SMD.pretty"),
        "C_0805_2012Metric_Pad1.18x1.45mm_HandSolder",
    ),
    "TH1": (
        os.path.join(HERE, "lib", "footprints.pretty"),
        "Thermistor_SEMITEC_103JT_Wired",
    ),
}


def footprint_blocks(text):
    """Return reference -> (start, end, block) for root-level footprints."""
    blocks = {}
    depth = 0
    start = None
    quoted = escaped = False
    i = 0
    while i < len(text):
        ch = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
        elif ch == '(':
            depth += 1
            if depth == 2 and text.startswith('(footprint ', i):
                start = i
        elif ch == ')':
            if depth == 2 and start is not None:
                end = i + 1
                block = text[start:end]
                match = re.search(r'\(property "Reference" "([^"]+)"', block)
                if match:
                    blocks[match.group(1)] = (start, end, block)
                start = None
            depth -= 1
        i += 1
    return blocks


def apply(check=False):
    board = pcbnew.LoadBoard(BOARD_PATH)
    by_ref = {fp.GetReference(): fp for fp in board.GetFootprints()}

    for ref, (libdir, name) in REPLACEMENTS.items():
        old = by_ref[ref]
        if old.GetFPID().GetLibItemName() == name:
            print(f"{ref}: already {name}")
            continue

        new = pcbnew.FootprintLoad(libdir, name)
        if new is None:
            raise SystemExit(f"could not load {name} from {libdir}")

        nets = {pad.GetPadName(): pad.GetNet() for pad in old.Pads()}
        new.SetReference(ref)
        new.SetValue(old.GetValue())
        new.SetPosition(old.GetPosition())
        new.SetOrientation(old.GetOrientation())
        new.SetLayer(old.GetLayer())
        for pad in new.Pads():
            net = nets.get(pad.GetPadName())
            if net is not None:
                pad.SetNet(net)

        board.Remove(old)
        board.Add(new)
        print(f"{ref}: {old.GetFPID().GetLibItemName()} -> {name}")

    with tempfile.NamedTemporaryFile(suffix=".kicad_pcb", delete=False) as fh:
        generated = fh.name
    pcbnew.SaveBoard(generated, board)

    # pcbnew.SaveBoard rewrites unrelated zone/layer state in this project.
    # Transplant only the requested root-level footprint expressions so the
    # rest of the hand-edited PCB remains byte-for-byte unchanged.
    original_text = open(BOARD_PATH).read()
    generated_text = open(generated).read()
    new_blocks = footprint_blocks(generated_text)
    old_blocks = footprint_blocks(original_text)
    edits = []
    for ref in REPLACEMENTS:
        start, end, _ = old_blocks[ref]
        edits.append((start, end, new_blocks[ref][2]))
    for start, end, block in sorted(edits, reverse=True):
        original_text = original_text[:start] + block + original_text[end:]

    out = "/tmp/moisture-bom-footprints.kicad_pcb" if check else BOARD_PATH
    with open(out, "w") as fh:
        fh.write(original_text)
    os.unlink(generated)
    print(f"wrote {out}")


if __name__ == "__main__":
    apply("--check" in sys.argv)
