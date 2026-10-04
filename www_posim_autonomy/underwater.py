"""Small BlueROV2 depth/heading controller: native ROS feedback, bounded thrust.

Teaching scaffold, not a complete competition solution. Improve estimation,
allocation and obstacle perception. Never controls the robot by setting poses.
"""
import argparse
import math
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray

from .control_math import allocate

class Controller(Node):
    def __init__(self,depth):
        super().__init__('www_posim_underwater');self.depth=depth;self.pose=None;self.received=0.;self.start=time.monotonic()
        self.pub=self.create_publisher(Float64MultiArray,'/wwos/thrusters',1)
        self.create_subscription(Odometry,'/model/bluerov2/odometry',self.receive,qos_profile_sensor_data)
        self.create_timer(.1,self.tick)
    def receive(self,msg):self.pose=msg;self.received=time.monotonic()
    def tick(self):
        values=[0.]*6
        if self.pose and time.monotonic()-self.received<.5:
            p=self.pose.pose.pose.position;v=self.pose.twist.twist.linear
            target=-self.depth if time.monotonic()-self.start<45 else 0.
            values=allocate(0.,0.,8*(target-p.z)-6*v.z)
        self.pub.publish(Float64MultiArray(data=values))

def main():
    p=argparse.ArgumentParser();p.add_argument('--depth',type=float,default=2);args=p.parse_args()
    if not 0<=args.depth<=5:p.error('Use a safe training depth of 0–5m.')
    rclpy.init();node=Controller(args.depth)
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:
        for _ in range(5):node.pub.publish(Float64MultiArray(data=[0.]*6))
        node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
