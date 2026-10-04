import unittest
from www_posim_autonomy.control_math import allocate
from www_posim_autonomy.planner import LaserPlanner

class Controls(unittest.TestCase):
 def test_downward_joints_require_negative_force_for_up(self):
  self.assertEqual(allocate(0,0,5),[0,0,0,0,-5,-5])
 def test_stock_horizontal_axis_signs(self):
  self.assertEqual(allocate(5,0,0),[-5,-5,5,5,0,0])
 def test_yaw_torque_signs(self):
  self.assertEqual(allocate(0,3,0),[-3,3,3,-3,0,0])
 def test_saturation(self):
  self.assertTrue(all(abs(v)<=20 for v in allocate(100,50,-100)))
 def test_lidar_map_forces_real_detour_and_return(self):
  p=LaserPlanner((0,0));p.observe([(12,0),(26,1)])
  self.assertFalse(p.clear_segment((0,0),(38,0)))
  for a,b in [((0,0),(38,0)),((38,0),(0,0))]:
   path=p.plan(a,b);self.assertTrue(path);self.assertGreater(max(abs(v[1]) for v in path),4)
   self.assertTrue(all(p.clear_segment(x,y) for x,y in zip(path,path[1:])))

if __name__=='__main__':unittest.main()
