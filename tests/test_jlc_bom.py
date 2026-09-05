import csv
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMATIC = ROOT / "moisture-sensor-carrier.kicad_sch"
MACOS_KICAD_CLI = Path(
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)


def find_kicad_cli() -> str | None:
    configured = os.environ.get("KICAD_CLI")
    if configured:
        return configured
    discovered = shutil.which("kicad-cli")
    if discovered:
        return discovered
    if MACOS_KICAD_CLI.is_file():
        return str(MACOS_KICAD_CLI)
    return None


class JlcBomTest(unittest.TestCase):
    def test_generated_bom_omits_non_purchasable_footprints(self) -> None:
        kicad_cli = find_kicad_cli()
        if kicad_cli is None:
            self.skipTest("kicad-cli is not installed")

        with tempfile.TemporaryDirectory() as directory:
            bom_path = Path(directory) / "bom.csv"
            subprocess.run(
                [
                    kicad_cli,
                    "sch",
                    "export",
                    "bom",
                    "--output",
                    str(bom_path),
                    "--exclude-dnp",
                    str(SCHEMATIC),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            with bom_path.open(newline="") as bom_file:
                references = {
                    reference
                    for row in csv.DictReader(bom_file)
                    for reference in row["Refs"].split(",")
                }

        self.assertTrue(
            {"AE1", "C29", "J5", "J4", "NT1", "NT2", "TP1", "TP2", "TP3"}.isdisjoint(
                references
            )
        )
        self.assertTrue({"U1", "R27", "X2", "L1", "FB1"}.isdisjoint(references))
        self.assertTrue({"U2", "U3", "U4", "X1", "C3"} <= references)


if __name__ == "__main__":
    unittest.main()
