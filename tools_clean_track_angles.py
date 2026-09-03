#!/usr/bin/env python3
"""Replace arbitrary-angle KiCad tracks with axial plus 45-degree legs.

The transformation changes only ``segment`` objects.  Width, layer, net and
all other properties are copied verbatim, and already-clean tracks are left
byte-for-byte unchanged.
"""

from __future__ import annotations

import argparse
import math
import re
import uuid
from pathlib import Path


SEGMENT = re.compile(
    r"(?P<body>\(segment\s+"
    r"\(start (?P<x1>[-\d.]+) (?P<y1>[-\d.]+)\)\s+"
    r"\(end (?P<x2>[-\d.]+) (?P<y2>[-\d.]+)\)"
    r"[\s\S]*?\n\s*\))"
)
TOLERANCE_DEGREES = 0.1


def _number(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def _clean_angle(a: tuple[float, float], b: tuple[float, float]) -> bool:
    angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 45
    return min(angle, 45 - angle) <= TOLERANCE_DEGREES


def _corner(a: tuple[float, float], b: tuple[float, float], strategy: str):
    dx, dy = b[0] - a[0], b[1] - a[1]
    adx, ady = abs(dx), abs(dy)
    sx = 1 if dx > 0 else -1
    sy = 1 if dy > 0 else -1
    if adx > ady:
        straight = (a[0] + sx * (adx - ady), a[1])
        diagonal = (b[0] - sx * (adx - ady), b[1])
    else:
        straight = (a[0], a[1] + sy * (ady - adx))
        diagonal = (b[0], b[1] - sy * (ady - adx))
    return straight if strategy == "straight" else diagonal


def _with_end(segment: str, end: tuple[float, float]) -> str:
    return re.sub(
        r"\(end [-\d.]+ [-\d.]+\)",
        f"(end {_number(end[0])} {_number(end[1])})",
        segment,
        count=1,
    )


def _with_start(segment: str, start: tuple[float, float]) -> str:
    result = re.sub(
        r"\(start [-\d.]+ [-\d.]+\)",
        f"(start {_number(start[0])} {_number(start[1])})",
        segment,
        count=1,
    )
    return re.sub(
        r'\(uuid "[^"]+"\)',
        f'(uuid "{uuid.uuid4()}")',
        result,
        count=1,
    )


def clean_track_angles(source: str, strategy: str = "straight") -> tuple[str, int]:
    if strategy not in {"straight", "diagonal"}:
        raise ValueError("strategy must be 'straight' or 'diagonal'")
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        a = (float(match.group("x1")), float(match.group("y1")))
        b = (float(match.group("x2")), float(match.group("y2")))
        segment = match.group("body")
        if _clean_angle(a, b):
            return segment
        corner = _corner(a, b, strategy)
        changed += 1
        first = _with_end(segment, corner)
        second = _with_start(segment, corner)
        return first + "\n\t" + second

    return SEGMENT.sub(replace, source), changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--strategy", choices=("straight", "diagonal"), default="straight")
    args = parser.parse_args()
    output, changed = clean_track_angles(args.input.read_text(), args.strategy)
    args.output.write_text(output)
    print(f"rewrote {changed} off-angle tracks in {args.output}")


if __name__ == "__main__":
    main()
