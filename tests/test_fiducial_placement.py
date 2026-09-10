import unittest
from pathlib import Path
from tools_sexp import parse,find,first
class FiducialPlacement(unittest.TestCase):
 def test_economic_assembly_has_no_copper_fiducials(self):
  root=Path(__file__).resolve().parents[1]
  board=parse((root/'nrf-moisture-sensor.kicad_pcb').read_text())
  self.assertFalse([fp for fp in find(board,'footprint') if fp[1].startswith('Fiducial:')])
  schematic=parse((root/'nrf-moisture-sensor.kicad_sch').read_text())
  self.assertFalse([s for s in find(schematic,'symbol') if first(s,'lib_id')==['lib_id','Mechanical:Fiducial']])

 def test_economic_tooling_holes(self):
  board=parse((Path(__file__).resolve().parents[1]/'nrf-moisture-sensor.kicad_pcb').read_text())
  holes=[fp for fp in find(board,'footprint') if fp[1]=='footprints:ToolingHole_JLC_1.152mm']
  self.assertEqual(len(holes),3)
  for fp in holes:
   pad=first(fp,'pad')
   self.assertEqual(pad[2:4],['np_thru_hole','circle'])
   self.assertEqual(float(first(pad,'drill')[1]),1.152)
   self.assertEqual(float(first(pad,'solder_mask_margin')[1]),0.148)
   self.assertEqual(first(pad,'layers'),['layers','*.Cu','*.Mask'])
   for attr in ['board_only','exclude_from_pos_files','exclude_from_bom']:
    self.assertIn(attr,first(fp,'attr'))
