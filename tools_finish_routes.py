#!/usr/bin/env python3
"""Historical finish-route helper (retired; production board is authoritative).

Every leg is axial or 45 degrees.  UUIDv5 identifiers make the operation
idempotent so the historical operation can be audited. The command-line entry
point is disabled because these coordinates must not overwrite hand-routed
production copper.
"""

from __future__ import annotations

import argparse
import re
import uuid
from pathlib import Path


# name, net, layer, width, points
ROUTES = [
    ("gnd_c11", "GND", "F.Cu", 0.40, [(75.305, 55.0008), (75.22, 55.0858), (75.22, 56.20)]),
    ("gnd_j4", "GND", "F.Cu", 0.40, [(84.665, 65.30), (83.965, 65.30)]),
    ("xc1", "/XC1", "F.Cu", 0.20, [(75.60, 60.079), (75.60, 58.775), (74.45, 57.625), (73.55, 57.625)]),
    ("swd_rst_top", "/SWD_RST", "F.Cu", 0.20, [(86.50, 62.76), (86.50, 62.76)]),
    ("swd_rst_bus", "/SWD_RST", "B.Cu", 0.20, [(86.50, 62.76), (87.30, 63.56), (87.30, 98.025), (86.00, 99.325), (71.325, 99.325)]),
    ("swd_rst_u2", "/SWD_RST", "F.Cu", 0.20, [(71.325, 99.325), (70.4625, 99.325)]),
    ("v3_pullups", "+3V3", "F.Cu", 0.40, [(71.00, 59.40), (71.00, 61.10), (70.9525, 61.10), (70.9525, 62.125)]),
    ("v3_u1", "+3V3", "F.Cu", 0.25, [(74.079, 65.20), (73.80, 65.479), (73.80, 65.90)]),
    ("deca_fb_bank", "/DECA", "F.Cu", 0.30, [(70.9285, 63.1444), (69.596, 63.1444), (69.1675, 62.7159), (69.1675, 61.90)]),
    ("decd_u1", "/DECD", "F.Cu", 0.19, [(74.079, 64.00), (73.60, 64.00), (73.20, 63.60), (72.5291, 63.60), (72.0735, 63.1444)]),
    ("decd_c1", "/DECD", "F.Cu", 0.30, [(69.4325, 66.30), (69.4325, 65.7854), (70.8035, 64.4144)]),
    ("fdc_u2_c26", "+3V3_FDC_SW", "F.Cu", 0.40, [(70.4625, 98.025), (71.00, 98.025), (72.00, 99.025), (72.00, 102.00), (73.00, 103.00), (76.4325, 103.00)]),
    ("fdc_u3_escape", "+3V3_FDC_SW", "F.Cu", 0.20, [(71.00, 106.40), (71.00, 105.50)]),
    ("fdc_trunk_join", "+3V3_FDC_SW", "F.Cu", 0.40, [(72.00, 102.00), (71.00, 103.00)]),
    ("fdc_escape_join", "+3V3_FDC_SW", "F.Cu", 0.20, [(71.00, 103.00), (71.00, 105.50)]),
    ("scl_u2", "/SCL", "F.Cu", 0.20, [(68.825, 100.9625), (68.825, 102.40)]),
    ("scl_u3", "/SCL", "F.Cu", 0.20, [(68.825, 102.40), (68.825, 103.975), (70.35, 105.50)]),
    ("scl_bus", "/SCL", "B.Cu", 0.20, [(74.822709, 58.582), (74.400709, 58.16), (62.30, 58.16), (62.30, 102.00), (68.425, 102.00), (68.825, 102.40)]),
    ("sda_u2", "/SDA", "F.Cu", 0.20, [(68.175, 100.9625), (68.175, 101.40)]),
    ("sda_u3", "/SDA", "F.Cu", 0.20, [(68.175, 101.40), (68.175, 104.575), (70.00, 106.40)]),
    ("sda_bus", "/SDA", "B.Cu", 0.20, [(73.00, 61.15), (73.80, 61.95), (73.80, 62.70), (63.10, 62.70), (63.10, 100.60), (67.375, 100.60), (68.175, 101.40)]),
]

# name, net, x, y, diameter, drill
VIAS = [
    ("gnd_c11", "GND", 75.22, 56.20, 0.60, 0.30),
    ("gnd_j4", "GND", 83.965, 65.30, 0.50, 0.20),
    ("swd_rst_top", "/SWD_RST", 86.50, 62.76, 0.50, 0.20),
    ("swd_rst_u2", "/SWD_RST", 71.325, 99.325, 0.50, 0.20),
    ("v3_u1", "+3V3", 73.80, 65.90, 0.60, 0.30),
    ("scl_u2", "/SCL", 68.825, 102.40, 0.50, 0.20),
    ("sda_u2", "/SDA", 68.175, 101.40, 0.50, 0.20),
]

NAMESPACE = uuid.UUID("24818857-cd65-4dd8-a731-e163ac6c58ad")


def _uid(kind: str, name: str, index: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{kind}:{name}:{index}"))


def _number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _generated_uuids() -> set[str]:
    ids = set()
    for name, _, _, _, points in ROUTES:
        ids.update(_uid("segment", name, index) for index in range(len(points) - 1))
    ids.update(_uid("via", name, 0) for name, *_ in VIAS)
    return ids


def _remove_generated(source: str) -> str:
    generated = _generated_uuids()
    pattern = re.compile(r"\t\((?:segment|via)\s+[\s\S]*?\n\t\)")
    def remove(match: re.Match[str]) -> str:
        block = match.group(0)
        if any(item in block for item in generated):
            return ""
        return block
    return pattern.sub(
        remove,
        source,
    )


def _segment(name, net, layer, width, start, end, index):
    return (
        "\t(segment\n"
        f"\t\t(start {_number(start[0])} {_number(start[1])})\n"
        f"\t\t(end {_number(end[0])} {_number(end[1])})\n"
        f"\t\t(width {_number(width)})\n"
        f"\t\t(layer \"{layer}\")\n"
        f"\t\t(net \"{net}\")\n"
        f"\t\t(uuid \"{_uid('segment', name, index)}\")\n"
        "\t)"
    )


def _via(name, net, x, y, diameter, drill):
    return (
        "\t(via\n"
        f"\t\t(at {_number(x)} {_number(y)})\n"
        f"\t\t(size {_number(diameter)})\n"
        f"\t\t(drill {_number(drill)})\n"
        "\t\t(layers \"F.Cu\" \"B.Cu\")\n"
        f"\t\t(net \"{net}\")\n"
        f"\t\t(uuid \"{_uid('via', name, 0)}\")\n"
        "\t)"
    )


def add_finish_routes(source: str) -> str:
    source = _remove_generated(source).rstrip()
    if not source.endswith(")"):
        raise ValueError("not a KiCad board")
    blocks = []
    for name, net, layer, width, points in ROUTES:
        for index, (start, end) in enumerate(zip(points, points[1:])):
            if start != end:
                blocks.append(_segment(name, net, layer, width, start, end, index))
    blocks.extend(_via(*via) for via in VIAS)
    return source[:-1].rstrip() + "\n" + "\n".join(blocks) + "\n)\n"


def main() -> None:
    raise SystemExit(
        "tools_finish_routes.py is retired: no scripted route writes are "
        "permitted on the production board."
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(add_finish_routes(args.input.read_text()))
    print(f"wrote {len(ROUTES)} route groups and {len(VIAS)} vias to {args.output}")


if __name__ == "__main__":
    main()
