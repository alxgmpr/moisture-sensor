#!/usr/bin/env python3
"""Regression checks for the nRF54L15 RF layout and switched FDC rail."""

import json
import math
import re
import unittest
from pathlib import Path

from tools_sexp import find, first, parse


ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "moisture-sensor-carrier.kicad_pcb"
PROJECT = ROOT / "moisture-sensor-carrier.kicad_pro"

LEGACY_NETS = (
    "FDC_VDD",
    "ANT_FEED",
    "RF_A",
    "RF_B",
    "GND_PA",
    "GND_C9",
)
CURRENT_NETS = {"+3V3_FDC_SW", "/XL1", "/XL2"}
RF_NETS = {"/ANT", "/RF_50R", "/RF_FILTER_N1", "/RF_FILTER_N2", "/RF_ANT"}


def properties(footprint):
    return {
        item[1]: item[2]
        for item in find(footprint, "property")
        if len(item) > 2
    }


def footprint_by_reference(board, reference):
    for footprint in find(board, "footprint"):
        if properties(footprint).get("Reference") == reference:
            return footprint
    raise AssertionError(f"missing footprint {reference}")


def pad_net(footprint, number):
    for pad in find(footprint, "pad"):
        if len(pad) > 1 and pad[1] == str(number):
            net = first(pad, "net")
            return net[1] if net else None
    raise AssertionError(f"missing pad {number}")


def footprint_position(footprint):
    transform = first(footprint, "transform")
    translate = first(transform, "translate")
    return float(translate[1]), float(translate[2])


class RfDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board_text = PCB.read_text()
        cls.board = parse(cls.board_text)
        cls.project = json.loads(PROJECT.read_text())

    def test_legacy_net_names_are_absent_from_design_sources(self):
        sources = [
            "moisture-sensor-carrier.kicad_sch",
            "moisture-sensor-carrier.kicad_pcb",
            "moisture-sensor-carrier.kicad_dru",
            "moisture-sensor-carrier.kicad_pro",
            "netlist-fingerprint.json",
            "tools_add_zones.py",
            "tools_dru_test.py",
            "tools_finish_routes.py",
            "tools_place_fixups.py",
            "tools_route.py",
            "HARDWARE.md",
            "LAYOUT.md",
            "NEXT-STEPS.md",
            "BOM.md",
        ]
        for relative_path in sources:
            text = (ROOT / relative_path).read_text()
            for legacy in LEGACY_NETS:
                with self.subTest(path=relative_path, net=legacy):
                    self.assertIsNone(
                        re.search(rf"(?<![A-Za-z0-9_]){re.escape(legacy)}(?![A-Za-z0-9_])", text)
                    )

    def test_new_net_names_observe_kicad_root_sheet_scope(self):
        board_nets = {
            first(node, "net")[1]
            for kind in ("segment", "via")
            for node in find(self.board, kind)
            if first(node, "net")
        }
        board_nets.update(
            net[1]
            for footprint in find(self.board, "footprint")
            for pad in find(footprint, "pad")
            if (net := first(pad, "net"))
        )
        self.assertTrue(CURRENT_NETS <= board_nets)
        self.assertNotIn("/+3V3_FDC_SW", board_nets)

    def test_switched_fdc_rail_and_i2c_pullups(self):
        u2 = footprint_by_reference(self.board, "U2")
        u3 = footprint_by_reference(self.board, "U3")
        c26 = footprint_by_reference(self.board, "C26")
        self.assertEqual(pad_net(u2, 12), "+3V3_FDC_SW")
        self.assertEqual(pad_net(u3, 8), "+3V3_FDC_SW")
        self.assertEqual(pad_net(c26, 1), "+3V3_FDC_SW")
        self.assertEqual({pad_net(footprint_by_reference(self.board, "R22"), 1),
                          pad_net(footprint_by_reference(self.board, "R23"), 1)}, {"+3V3"})

    def test_orderable_jlc3313_stackup_is_recorded_exactly(self):
        stackup = first(first(self.board, "setup"), "stackup")
        layers = {layer[1]: layer for layer in find(stackup, "layer")}
        expected = {
            "F.Cu": ("copper", 0.035, None, None),
            "dielectric 1": ("prepreg", 0.0994, "FR4 3313 RC57%", 4.1),
            "In1.Cu": ("copper", 0.0152, None, None),
            "dielectric 2": ("core", 1.265, "FR4", 4.6),
            "In2.Cu": ("copper", 0.0152, None, None),
            "dielectric 3": ("prepreg", 0.0994, "FR4 3313 RC57%", 4.1),
            "B.Cu": ("copper", 0.035, None, None),
        }
        for name, (kind, thickness, material, epsilon_r) in expected.items():
            with self.subTest(layer=name):
                layer = layers[name]
                self.assertEqual(first(layer, "type")[1], kind)
                self.assertAlmostEqual(float(first(layer, "thickness")[1]), thickness, places=5)
                if material:
                    self.assertEqual(first(layer, "material")[1], material)
                    self.assertAlmostEqual(float(first(layer, "epsilon_r")[1]), epsilon_r)


if __name__ == "__main__":
    unittest.main()
