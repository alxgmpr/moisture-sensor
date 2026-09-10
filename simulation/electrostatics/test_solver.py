import unittest
import numpy as np
from solver import solve
class PlateTest(unittest.TestCase):
 def test_parallel_plate_charge(self):
  eps=np.full((21,11),4.0); fixed=np.full(eps.shape,np.nan)
  fixed[:,0]=0;fixed[:,-1]=1
  voltage,charge=solve(eps,fixed)
  np.testing.assert_allclose(voltage,np.tile(np.linspace(0,1,11),(21,1)),atol=1e-8)
  self.assertAlmostEqual(charge[:,-1].sum(),21*4/10,places=7)
if __name__=='__main__': unittest.main()
