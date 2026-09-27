import tempfile,unittest
from pathlib import Path
from tools_export_jlc_economic import fabrication_files, accepted_error
class QuoteArchive(unittest.TestCase):
 def test_only_user_accepted_vias_can_bypass_error_gate(self):
  import copy
  violation={'type':'items_not_allowed','items':[{'uuid':'0c92937a-92ec-40d8-8988-a4f1037265c0','description':'Via [+3V3] on F.Cu - B.Cu','pos':{'x':74.475,'y':72.675}}]}
  self.assertTrue(accepted_error(violation))
  for field,value in [('uuid','different-via'),('description','Via [GND] on F.Cu - B.Cu'),('pos',{'x':74.475,'y':70})]:
   changed=copy.deepcopy(violation);changed['items'][0][field]=value
   self.assertFalse(accepted_error(changed))
  violation['type']='clearance'
  self.assertFalse(accepted_error(violation))
 def test_old_board_files_cannot_enter_new_archive(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   for layer,ext in [('F_Cu','.gtl'),('B_Cu','.gbl'),('GND','.g1'),('GND-SHLD','.g2'),('F_Mask','.gts'),('B_Mask','.gbs'),('F_Silkscreen','.gto'),('B_Silkscreen','.gbo'),('F_Paste','.gtp'),('B_Paste','.gbp'),('Edge_Cuts','.gm1'),('PTH','.drl'),('NPTH','.drl')]:
    (p/f'nrf-moisture-sensor-{layer}{ext}').touch()
    (p/f'moisture-sensor-{layer}{ext}').touch()
   files=fabrication_files(p)
   self.assertEqual(len(files),13)
   self.assertTrue(all(f.name.startswith('nrf-moisture-sensor-') for f in files))
   files[0].unlink()
   with self.assertRaises(AssertionError): fabrication_files(p)
