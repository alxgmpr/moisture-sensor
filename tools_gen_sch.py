#!/usr/bin/env python3
"""Retired schematic generator.

The historic generator described an nPM1300 design and cannot reproduce the
maintained nPM2100 schematic.  It is intentionally non-operational so running
it can never overwrite the authoritative KiCad source.
"""


def main() -> int:
    raise SystemExit(
        "Retired: tools_gen_sch.py cannot reproduce the current nPM2100 design "
        "and will not modify moisture-sensor-carrier.kicad_sch."
    )


if __name__ == "__main__":
    main()
