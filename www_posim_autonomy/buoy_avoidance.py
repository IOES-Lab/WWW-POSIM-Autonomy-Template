#!/usr/bin/env python3
"""Local participant ROS2 node: laser -> map -> A* -> body velocity commands.

Run alongside relay.py --control in your own ROS domain. No ArduPilot imports,
HTTP mission calls, buoy coordinates, pose writes or server code execution.
"""
import argparse
import json
import math
from pathlib import Path
import time
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped
from .planner import LaserPlanner, yaw, steering

class Participant(Node):
    def __init__(self,args):
        super().__init__('wwos_buoy_avoidance');self.args=args
        self.odom=None;self.odom_at=0.;self.scan_at=0.;self.scan_count=0;self.laser_hits=0
        self.planner=None;self.path=[];self.path_at=0.;self.path_revision=-1
        self.goal_index=0;self.goals=[];self.trace=[];self.started=time.monotonic();self.sim_start=None;self.elapsed_sim=0.;self.completed=False
        self.publisher=self.create_publisher(TwistStamped,'/wwos/cmd_vel',1)
        self.create_subscription(Odometry,'/model/wamv/odometry',self.receive_pose,qos_profile_sensor_data)
        self.create_subscription(LaserScan,'/model/wamv/scan',self.receive_scan,qos_profile_sensor_data)
        self.timer=self.create_timer(.1,self.tick)
    def receive_pose(self,msg):
        self.odom=msg;self.odom_at=time.monotonic()
        stamp=msg.header.stamp.sec+msg.header.stamp.nanosec/1e9
        if self.sim_start is None:self.sim_start=stamp
        self.elapsed_sim=max(0.,stamp-self.sim_start)
        if self.planner is None:
            p=msg.pose.pose.position;self.planner=LaserPlanner((p.x,p.y))
            self.goals=[(p.x+self.args.distance,p.y),(p.x,p.y)]
    def receive_scan(self,msg):
        if self.odom is None or time.monotonic()-self.odom_at>.5:return
        self.scan_at=time.monotonic();self.scan_count+=1
        p=self.odom.pose.pose.position;q=self.odom.pose.pose.orientation
        # Rotate actual sensor rays by the measured 3D robot attitude. The
        # known sensor extrinsic is (0,0,2.5), not obstacle ground truth.
        from scipy.spatial.transform import Rotation
        import numpy as np
        rot=Rotation.from_quat([q.x,q.y,q.z,q.w]);points=[]
        sensor=rot.apply([0,0,2.5])+[p.x,p.y,p.z]
        for i,r in enumerate(msg.ranges):
            if not math.isfinite(r) or not msg.range_min<r<min(msg.range_max-.1,45):continue
            angle=msg.angle_min+i*msg.angle_increment
            endpoint=rot.apply([r*math.cos(angle),r*math.sin(angle),0])+sensor
            # Reject sea-surface returns; tall buoy/land returns remain. Real
            # sensors require richer water/ground filtering and covariance.
            if endpoint[2]>.8:points.append(tuple(endpoint[:2]))
        self.laser_hits+=len(points);self.planner.observe(points)
    def send(self,speed=0.,turn=0.):
        msg=TwistStamped();msg.header.stamp=self.get_clock().now().to_msg();msg.header.frame_id='base_link'
        msg.twist.linear.x=float(speed);msg.twist.angular.z=float(turn);self.publisher.publish(msg)
    def tick(self):
        now=time.monotonic()
        if self.completed:self.send();return
        if self.elapsed_sim>self.args.timeout:
            self.send();self.completed=True;return
        if self.odom is None or now-self.odom_at>.5 or now-self.scan_at>.5 or self.scan_count<3:
            self.send();return
        p=self.odom.pose.pose.position;position=(p.x,p.y);heading=yaw(self.odom.pose.pose.orientation)
        goal=self.goals[self.goal_index]
        if math.dist(position,goal)<1.5:
            self.goal_index+=1;self.path=[]
            if self.goal_index==len(self.goals):self.completed=True;self.send();self.get_logger().info('Returned to start');return
            goal=self.goals[self.goal_index]
        if now-self.path_at>.5 or self.path_revision!=self.planner.revision:
            self.path=self.planner.plan(position,goal);self.path_at=now;self.path_revision=self.planner.revision
        speed,turn=steering(position,heading,self.path,self.args.speed)
        self.send(speed,turn)
        self.trace.append({'wall_seconds':now-self.started,'sim_seconds':self.elapsed_sim,'x':p.x,'y':p.y,'z':p.z,'yaw':heading,'phase':self.goal_index,'speed_command':speed,'yaw_rate_command':turn,'scan_age':now-self.scan_at,'path_points':len(self.path),'known_obstacle_cells':len(self.planner.occupied)})
    def report(self):return {'completed':self.completed and self.goal_index==len(self.goals),'reached_goals':self.goal_index,'scan_messages':self.scan_count,'laser_returns':self.laser_hits,'obstacle_cells':len(self.planner.occupied) if self.planner else 0,'trace':self.trace,'uses_ardupilot':False,'obstacle_source':'Gazebo LaserScan only'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--distance',type=float,default=38);parser.add_argument('--speed',type=float,default=.8)
    parser.add_argument('--timeout',type=float,default=240);parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    if not 32<=args.distance<=50 or not .2<=args.speed<=1.:parser.error('Use 32–50m and 0.2–1m/s for this bounded example')
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO);node=Participant(args)
    try:
        while rclpy.ok() and not node.completed:rclpy.spin_once(node,timeout_sec=.1)
    except KeyboardInterrupt:pass
    finally:
        node.timer.cancel()
        # Keep ROS alive until neutral messages have left; its default SIGINT
        # handler otherwise closes the context before this cleanup runs.
        for _ in range(5):node.send();rclpy.spin_once(node,timeout_sec=.05)
        if args.report:args.report.write_text(json.dumps(node.report(),indent=2))
        node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
