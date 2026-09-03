#!/usr/bin/env python3
"""PCB-side exclusions for footprints that are not assembled parts."""

import unittest
from pathlib import Path

from tools_sexp import find, first, parse


ROOT = Path(__file__).resolve().parents[1]
NON_ASSEMBLY_REFERENCES = {"J4", "NT1", "NT2", "TP1", "TP2", "TP3"}
REQUIRED_ATTRIBUTES = {"exclude_from_bom", "exclude_from_pos_files"}


class PcbAssemblyFlagsTest(unittest.TestCase):
    def test_bare_copper_footprints_are_excluded_from_assembly_outputs(self):
        board = parse((ROOT / "moisture-sensor-carrier.kicad_pcb").read_text())
        checked = set()
        for footprint in find(board, "footprint"):
            properties = {
                item[1]: item[2]
                for item in find(footprint, "property")
                if len(item) > 2
            }
            reference = properties.get("Reference")
            if reference not in NON_ASSEMBLY_REFERENCES:
                continue
            attributes_node = first(footprint, "attr")
            attributes = set(attributes_node[1:] if attributes_node else [])
            self.assertTrue(
                REQUIRED_ATTRIBUTES <= attributes,
                f"{reference} has attributes {sorted(attributes)}",
            )
            checked.add(reference)
        self.assertEqual(checked, NON_ASSEMBLY_REFERENCES)

    def test_board_generator_reapplies_non_assembly_flags(self):
        source = (ROOT / "tools_gen_pcb.py").read_text()
        self.assertIn("NON_ASSEMBLY_REFERENCES", source)
        self.assertIn("FP_EXCLUDE_FROM_BOM", source)
        self.assertIn("FP_EXCLUDE_FROM_POS_FILES", source)


if __name__ == "__main__":
    unittest.main()
