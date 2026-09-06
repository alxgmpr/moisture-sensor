#!/usr/bin/env python3
"""Regression checks for JLCPCB routing classes and net assignments."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "nrf-moisture-sensor.kicad_pro"


class PcbRoutingRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        project = json.loads(PROJECT.read_text())
        settings = project["net_settings"]
        cls.classes = {item["name"]: item for item in settings["classes"]}
        cls.assignments = {
            item["pattern"]: item["netclass"]
            for item in settings["netclass_patterns"]
        }

    def test_routing_classes_use_production_safe_dimensions(self):
        expected = {
            "Default": (0.20, 0.20, 0.50, 0.20),
            "Control": (0.20, 0.20, 0.50, 0.20),
            "I2C": (0.20, 0.20, 0.50, 0.20),
            "Crystal": (0.20, 0.20, 0.50, 0.20),
            "LocalPower": (0.30, 0.20, 0.60, 0.30),
            "Power": (0.40, 0.25, 0.60, 0.30),
            "SENSE": (0.25, 0.60, 0.50, 0.20),
            "SHIELD": (0.30, 0.20, 0.60, 0.30),
            "SWITCH": (0.50, 0.30, 0.60, 0.30),
        }
        self.assertEqual(set(self.classes), set(expected))
        for name, dimensions in expected.items():
            with self.subTest(netclass=name):
                item = self.classes[name]
                actual = (
                    item["track_width"],
                    item["clearance"],
                    item["via_diameter"],
                    item["via_drill"],
                )
                self.assertEqual(actual, dimensions)

    def test_every_connected_net_has_an_explicit_class(self):
        expected = {
            "+3V3": "Power",
            "/NRESET": "Control",
            "/P2.07_SWO": "Control",
            "/PMIC_INT": "Control",
            "/SCL": "I2C",
            "/SDA": "I2C",
            "/SENSE1": "SENSE",
            "/SENSE2": "SENSE",
            "/SHLD": "SHIELD",
            "/SW": "SWITCH",
            "/SWDCLK": "Control",
            "/SWDIO": "Control",
            "/SWD_RST": "Control",
            "/VINT": "LocalPower",
            "/XL1": "Crystal",
            "/XL2": "Crystal",
            "+3V3_FDC_SW": "Power",
            "GND": "Power",
            "VBAT": "Power",
            "/VBAT_RAW": "Power",
            "/CIN1_PROTECTED": "SENSE",
            "/CIN2_PROTECTED": "SENSE",
            "/SWDIO_EXT": "Control",
            "/SWDCLK_EXT": "Control",
            "/SWO_EXT": "Control",
            "/RESET_EXT": "Control",
        }
        self.assertEqual(self.assignments, expected)

    def test_retired_power_nets_are_not_assigned(self):
        retired = {
            "/SW2",
            "/GND_PVSS2",
            "SOLAR_5V",
            "SOLAR_PANEL",
            "VBUS_IN",
            "VSYS",
        }
        self.assertTrue(retired.isdisjoint(self.assignments))

    def test_router_does_not_reference_retired_switch_net(self):
        router = (ROOT / "tools_route.py").read_text()
        self.assertNotIn('"/SW2"', router)

    def test_hole_spacing_matches_jlcpcb_four_layer_capability(self):
        project = json.loads(PROJECT.read_text())
        rules = project["board"]["design_settings"]["rules"]
        self.assertEqual(rules["min_hole_to_hole"], 0.20)


if __name__ == "__main__":
    unittest.main()
