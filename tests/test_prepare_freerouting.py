import unittest

from tools_prepare_freerouting import prepare_dsn


class PrepareFreeroutingTests(unittest.TestCase):
    def test_removes_exported_polygon_wires(self):
        source = """(pcb demo
  (wiring
    (wire (polygon F.Cu 0 0 0 10 0 10 10)(net GND)(type protect))
    (wire (polygon F.Cu 0 0 0 10000 0 10000 10000)(net GND)(type protect))
    (wire (path F.Cu 200 0 0 10 0)(net /SDA)(type protect))
  )
)"""
        result = prepare_dsn(source)
        self.assertNotIn("0 0 0 10 0 10 10", result)
        self.assertIn("0 0 0 10000 0 10000 10000", result)
        self.assertIn("(wire (path F.Cu 200", result)

    def test_unlocks_only_noncritical_routes(self):
        source = """(pcb demo
  (wiring
    (wire (path F.Cu 200 0 0 10 0)(net /SDA)(type protect))
    (wire (path F.Cu 360 0 1 10 1)(net /RF_FILTER_N1)(type protect))
    (via Via[0-3]_600:300_um 5 5 (net /SCL) (type protect))
    (via Via[0-3]_600:300_um 6 6 (net GND) (type protect))
  )
)"""
        result = prepare_dsn(source, unlock_noncritical=True)
        self.assertIn("(net /SDA))", result)
        self.assertIn("(net /RF_FILTER_N1)(type protect)", result)
        self.assertIn("(net /SCL))", result)
        self.assertIn("(net GND) (type protect)", result)

    def test_keeps_routes_protected_by_default(self):
        source = """(pcb demo (wiring
          (wire (path F.Cu 200 0 0 10 0)(net /SDA)(type protect))
        ))"""
        self.assertIn("(type protect)", prepare_dsn(source))


if __name__ == "__main__":
    unittest.main()
