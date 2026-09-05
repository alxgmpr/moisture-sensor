"""Integration checks against Ezurio BL54L15 453-00001 pin table and land drawing."""
import unittest
from pathlib import Path
from tools_sexp import parse, find, first
ROOT=Path(__file__).resolve().parents[1]
class BL54L15Test(unittest.TestCase):
 def test_module_pads_preserve_product_signals(self):
  b=parse((ROOT/'moisture-sensor-carrier.kicad_pcb').read_text())
  fps={dict((p[1],p[2]) for p in find(f,'property')).get('Reference'):f for f in find(b,'footprint')}
  u=fps['U1']
  self.assertEqual(u[1],'footprints:Ezurio_BL54L15_453-00001')
  nets={p[1]:first(p,'net')[1] for p in find(u,'pad') if first(p,'net')}
  for pin,net in {'1':'GND','16':'GND','27':'GND','39':'GND','26':'+3V3','25':'/XL1','24':'/XL2','35':'/SCL','28':'/SDA','17':'/PMIC_INT','4':'/P2.07_SWO','5':'/SWDIO','6':'/SWDCLK','7':'/NRESET'}.items():
   with self.subTest(pin=pin):self.assertEqual(nets[pin],net)
  self.assertFalse(set(fps)&{'AE1','X2','L1','L2','L3','L4','FB1','C1','C2','C4','C5','C6','C7','C8','C9','C10','C11','C12','C29','R27','NT1','NT2'})
 def test_vendor_land_pattern(self):
  path=ROOT/'lib/footprints.pretty/Ezurio_BL54L15_453-00001.kicad_mod'
  self.assertTrue(path.is_file(),'Verified BL54L15 footprint is missing')
  f=parse(path.read_text());pads={p[1]:p for p in find(f,'pad')}
  self.assertEqual(set(pads),set(map(str,range(1,40))))
  for n,xy in {'1':(11.8,9.497),'16':(.55,9.497),'17':(.5,8.75),'26':(.5,2.0),'27':(.5,1.25),'28':(.55,.503),'39':(8.8,.503)}.items():
   with self.subTest(pin=n):
    self.assertEqual(tuple(map(float,first(pads[n],'at')[1:3])),xy)
  for p in pads.values():
   self.assertEqual(tuple(map(float,first(p,'size')[1:3])),(.45,.6))
   self.assertEqual(set(first(p,'layers')[1:]),{'F.Cu','F.Paste','F.Mask'})
 def test_all_land_centers_and_antenna_rules(self):
  f=parse((ROOT/'lib/footprints.pretty/Ezurio_BL54L15_453-00001.kicad_mod').read_text())
  for pad in find(f,'pad'):
   n=int(pad[1]);at=first(pad,'at')
   if n<=16:expected=(11.8-.75*(n-1),9.497)
   elif n<=27:expected=(.5,8.75-.75*(n-17))
   else:expected=(.55+.75*(n-28),.503)
   for actual,wanted in zip(map(float,at[1:3]),expected):self.assertAlmostEqual(actual,wanted,places=6)
  b=parse((ROOT/'moisture-sensor-carrier.kicad_pcb').read_text())
  keepouts=[z for z in find(b,'zone') if first(z,'name') and first(z,'name')[1].startswith('BL54L15_AntennaKeepout')]
  self.assertEqual(len(keepouts),1)  # One rule area for the manufacturer hatched region.
  for z in keepouts:
   self.assertEqual(set(first(z,'layers')[1:]),{'F.Cu','In1.Cu','In2.Cu','B.Cu'})
   for feature in ['tracks','vias','pads','copperpour']:
    self.assertEqual(first(first(z,'keepout'),feature)[1],'not_allowed')
if __name__=='__main__':unittest.main()
