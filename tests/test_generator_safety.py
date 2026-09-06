#!/usr/bin/env python3
"""Ensure stale one-shot generators cannot overwrite maintained design files."""

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GeneratorSafetyTest(unittest.TestCase):
    def test_retired_schematic_generator_exits_without_modifying_schematic(self):
        schematic = ROOT / "nrf-moisture-sensor.kicad_sch"
        before = schematic.read_bytes()
        result = subprocess.run(
            ["python3", str(ROOT / "tools_gen_sch.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retired", (result.stdout + result.stderr).lower())
        self.assertEqual(schematic.read_bytes(), before)

    def test_retired_board_helpers_exit_without_modifying_the_board(self):
        board = ROOT / "nrf-moisture-sensor.kicad_pcb"
        before = board.read_bytes()
        for script in (
            "tools_gen_pcb.py",
            "tools_route.py",
            "tools_finish_routes.py",
            "tools_add_zones.py",
            "tools_place_fixups.py",
        ):
            with self.subTest(script=script):
                result = subprocess.run(
                    ["python3", str(ROOT / script)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("retired", (result.stdout + result.stderr).lower())
                self.assertEqual(board.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
