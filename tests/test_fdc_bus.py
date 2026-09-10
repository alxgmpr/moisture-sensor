"""Keep the switched FDC isolated from the PMIC's always-powered bus."""
import unittest
from tools_netcmp import netlist
from tools_sexp import parse, find, first
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FdcBusTest(unittest.TestCase):
    def test_dedicated_bus_and_pullup_supplies(self):
        nets = netlist()
        self.assertEqual(set(nets['FDC_SDA']), {'U1.22', 'U3.10', 'R36.2'})
        self.assertEqual(set(nets['FDC_SCL']), {'U1.23', 'U3.9', 'R37.2'})
        self.assertTrue({'R36.1', 'R37.1', 'U3.8'} <= set(nets['+3V3_FDC_SW']))
        self.assertTrue({'R22.1', 'R23.1'} <= set(nets['+3V3']))
        self.assertEqual(set(nets['SDA']), {'U1.28', 'U2.6', 'U4.1', 'R22.2', 'TP12.1'})
        self.assertEqual(set(nets['SCL']), {'U1.35', 'U2.7', 'U4.2', 'R23.2', 'TP13.1'})

    def test_board_pads_match_the_split(self):
        board = parse((ROOT / 'nrf-moisture-sensor.kicad_pcb').read_text())
        nets = {}
        for fp in find(board, 'footprint'):
            ref = next(p[2] for p in find(fp, 'property') if p[1] == 'Reference')
            for pad in find(fp, 'pad'):
                if first(pad, 'net'):
                    nets[f'{ref}.{pad[1]}'] = first(pad, 'net')[1]
        for pin in ['U1.22', 'U3.10', 'R36.2']:
            self.assertEqual(nets[pin], '/FDC_SDA')
        for pin in ['U1.23', 'U3.9', 'R37.2']:
            self.assertEqual(nets[pin], '/FDC_SCL')
        for pin in ['R36.1', 'R37.1', 'U3.8']:
            self.assertEqual(nets[pin], '+3V3_FDC_SW')


if __name__ == '__main__':
    unittest.main()
