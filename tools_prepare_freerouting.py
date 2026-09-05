#!/usr/bin/env python3
"""Prepare a KiCad Specctra export for a useful Freerouting pass.

KiCad exports filled zones and teardrops as protected polygon wires.  Those
objects are already represented by board geometry and make Freerouting spend
most of its time trying to connect artificial items.  Remove them, and unlock
ordinary tracks/vias while retaining the deliberately hand-routed critical
nets.

Usage:
    python3 tools_prepare_freerouting.py input.dsn output.dsn
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PROTECTED_NETS = {
    "+3V3",
    "/ANT",
    "/RF_50R",
    "/DCC",
    "/DECA",
    "/DECD",
    "/RF_C9_RETURN_BOTTOM",
    "/RF_PA_RETURN_LOCAL",
    "/RF_FILTER_N1",
    "/RF_FILTER_N2",
    "/SENSE1",
    "/SENSE2",
    "/SHLD",
    "/SW",
    "/VINT",
    "+3V3_FDC_SW",
    "GND",
    "VBAT",
}


def _expressions(source: str, tag: str):
    """Yield balanced S-expression spans beginning with *tag*."""
    for match in re.finditer(r"\(" + re.escape(tag) + r"\b", source):
        depth = 0
        quoted = False
        escaped = False
        for index in range(match.start(), len(source)):
            char = source[index]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    yield match.start(), index + 1, source[match.start() : index + 1]
                    break


def _net_name(expression: str) -> str | None:
    match = re.search(r"\(net\s+(\"[^\"]+\"|[^\s)]+)\)", expression)
    if not match:
        return None
    return match.group(1).strip('"')


def _is_generated_small_polygon(expression: str, threshold_um: float = 3000) -> bool:
    header = expression.split("(net", 1)[0]
    numbers = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", header)]
    # The first number is the polygon aperture width; the rest are x/y pairs.
    coordinates = numbers[1:]
    if len(coordinates) < 6:
        return True
    xs = coordinates[0::2]
    ys = coordinates[1::2]
    return max(xs) - min(xs) < threshold_um and max(ys) - min(ys) < threshold_um


def prepare_dsn(source: str, *, unlock_noncritical: bool = False) -> str:
    edits: list[tuple[int, int, str]] = []
    for tag in ("wire", "via"):
        for start, end, expression in _expressions(source, tag):
            if tag == "wire" and re.match(r"\(wire\s+\(polygon\b", expression):
                if _is_generated_small_polygon(expression):
                    edits.append((start, end, ""))
                continue
            net = _net_name(expression)
            if unlock_noncritical and net is not None and net not in PROTECTED_NETS:
                unlocked = re.sub(r"\s*\(type\s+protect\)", "", expression)
                edits.append((start, end, unlocked))

    result = source
    for start, end, replacement in sorted(edits, reverse=True):
        result = result[:start] + replacement + result[end:]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--unlock-noncritical",
        action="store_true",
        help="allow Freerouting to rip up ordinary signal tracks and vias",
    )
    args = parser.parse_args()
    args.output.write_text(
        prepare_dsn(args.input.read_text(), unlock_noncritical=args.unlock_noncritical)
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
