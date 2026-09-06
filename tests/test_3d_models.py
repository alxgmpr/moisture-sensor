#!/usr/bin/env python3
"""Regression checks for fitted-component 3D model coverage."""

import unittest
from pathlib import Path

from tools_sexp import find, first, parse


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "nrf-moisture-sensor.kicad_pcb"
KICAD_MODELS = Path(
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels"
)

EXPECTED_PROJECT_MODELS = {
    "BT1": "${KIPRJMOD}/lib/CR2032-BS-6-1_C70377.step",
    "L10": "${KIPRJMOD}/lib/DFE201210U_2R2M_P2/IND_DFE201210U-2R2MP2_MUR.step",
    "U1": "${KIPRJMOD}/lib/BL54L15_453-00001.step",
    "U4": "${KIPRJMOD}/lib/SHT45_AD1F_R2/SHT45-AD1F-R2.step",
    "X1": "${KIPRJMOD}/lib/CM8V-T1A/CM8V-T1A-32.768KHZ-7PF-20PPM-TA-QC.step",
}
EXPECTED_U2_MODEL = (
    "${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/"
    "Texas_RSA_VQFN-16-1EP_4x4mm_P0.65mm_EP2.7x2.7mm.step"
)
NO_MODEL_EXPECTED = {"J4", "TP1", "TP2", "TP3", "FID1", "FID2", "FID3", "FID4", "REF**"}


def board_footprints():
    board = parse(BOARD.read_text())
    result = {}
    for footprint in find(board, "footprint"):
        properties = {
            item[1]: item[2]
            for item in find(footprint, "property")
            if len(item) > 2
        }
        result[properties["Reference"]] = footprint
    return result


def model_paths(footprint):
    return [model[1] for model in find(footprint, "model")]


def model_rotation(footprint):
    model = find(footprint, "model")[0]
    return tuple(float(value) for value in first(first(model, "rotate"), "xyz")[1:])


def resolve_model(path):
    path = path.replace("${KIPRJMOD}", str(ROOT))
    path = path.replace("${KICAD10_3DMODEL_DIR}", str(KICAD_MODELS))
    return Path(path)


class ModelCoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.footprints = board_footprints()

    def test_selected_parts_use_one_expected_model_each(self):
        expected = dict(EXPECTED_PROJECT_MODELS)
        expected["U2"] = EXPECTED_U2_MODEL
        for reference, path in expected.items():
            with self.subTest(reference=reference):
                self.assertEqual(model_paths(self.footprints[reference]), [path])

    def test_ezurio_library_and_board_share_vendor_alignment(self):
        library = parse((ROOT / "lib/footprints.pretty/Ezurio_BL54L15_453-00001.kicad_mod").read_text())
        for footprint in (library, self.footprints["U1"]):
            self.assertEqual(model_paths(footprint), [EXPECTED_PROJECT_MODELS["U1"]])
            model = find(footprint, "model")[0]
            self.assertEqual(tuple(float(v) for v in first(first(model, "offset"), "xyz")[1:]),
                             (0, -10, 0.40116))

    def test_selected_models_are_on_the_component_side(self):
        expected_rotations = {
            "BT1": (0.0, 0.0, 180.0),
            "L10": (0.0, 0.0, 0.0),
            "U1": (0.0, 0.0, 0.0),
            "U2": (0.0, 0.0, 0.0),
            "U4": (-90.0, 0.0, 0.0),
            "X1": (-90.0, 0.0, 0.0),
        }
        for reference, rotation in expected_rotations.items():
            with self.subTest(reference=reference):
                self.assertEqual(model_rotation(self.footprints[reference]), rotation)

    def test_all_referenced_model_files_exist(self):
        for reference, footprint in self.footprints.items():
            for path in model_paths(footprint):
                with self.subTest(reference=reference, path=path):
                    self.assertTrue(resolve_model(path).is_file(), path)

    def test_only_bare_copper_footprints_are_model_less(self):
        missing = {
            reference
            for reference, footprint in self.footprints.items()
            if not model_paths(footprint)
        }
        self.assertEqual(missing, NO_MODEL_EXPECTED)

    def test_model_tools_do_not_reference_retired_packages(self):
        sources = "\n".join(
            (ROOT / name).read_text()
            for name in ("tools_3d_models.py", "tools_gen_pcb.py")
        )
        for retired in (
            "QFN32_5X5_NOR.step",
            "TYPE-C-31-M-12--3DModel-STEP-56544.STEP",
            "WLCSP_1p9x1p9_NOR.step",
        ):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, sources)

    def test_custom_footprints_keep_their_models(self):
        expected = {
            "BatteryHolder_LianXin_CR2032-BS-6.kicad_mod": (
                EXPECTED_PROJECT_MODELS["BT1"], (0.0, 0.0, 180.0)),
            "IND_Murata_DFE201210U.kicad_mod": (
                EXPECTED_PROJECT_MODELS["L10"], (0.0, 0.0, 0.0)),
            "XTAL_CM8V-T1A_2012.kicad_mod": (
                EXPECTED_PROJECT_MODELS["X1"], (-90.0, 0.0, 0.0)),
            "XTAL_FA-128_2016_4Pin.kicad_mod": (
                "${KIPRJMOD}/lib/FA-128 32.0000MF10Z-AJ0.STEP", (-90.0, 0.0, 90.0)),
        }
        for filename, (path, rotation) in expected.items():
            with self.subTest(filename=filename):
                footprint = parse(
                    (ROOT / "lib" / "footprints.pretty" / filename).read_text()
                )
                self.assertEqual([model[1] for model in find(footprint, "model")], [path])
                self.assertEqual(model_rotation(footprint), rotation)

    def test_symbol_library_table_only_lists_current_project_libraries(self):
        table = parse((ROOT / "sym-lib-table").read_text())
        libraries = {
            first(item, "name")[1]: first(item, "uri")[1]
            for item in find(table, "lib")
        }
        self.assertEqual(
            libraries,
            {
                "ezurio": "${KIPRJMOD}/lib/ezurio.kicad_sym",
                "npm2100": "${KIPRJMOD}/lib/nordic/NPM2100-QEAA.kicad_sym",
                "fdc": "${KIPRJMOD}/lib/FDC1004.kicad_sym",
                "sht4x": "${KIPRJMOD}/lib/SHT4x.kicad_sym",
                "power_local": "${KIPRJMOD}/lib/power_local.kicad_sym",
                "protection": "${KIPRJMOD}/lib/protection.kicad_sym",
            },
        )
        for uri in libraries.values():
            self.assertTrue(resolve_model(uri).is_file(), uri)

    def test_incompatible_downloaded_packages_are_not_kept(self):
        self.assertFalse((ROOT / "lib" / "NPM2100_QEAA_R7").exists())


if __name__ == "__main__":
    unittest.main()
