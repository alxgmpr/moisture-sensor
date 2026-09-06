#!/usr/bin/env python3
"""Retired PCB generator.

The historic one-shot generator predates the maintained nRF54L15/nPM2100
layout, integrated PCB antenna path, and controlled-impedance stackup.  It is
intentionally non-operational so it cannot overwrite hand-routed board data.
"""


def main() -> int:
    raise SystemExit(
        "Retired: tools_gen_pcb.py cannot reproduce the current hand-routed "
        "design and will not modify nrf-moisture-sensor.kicad_pcb."
    )


if __name__ == "__main__":
    main()
