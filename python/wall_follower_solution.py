#!/usr/bin/env python
import rospy
from std_msgs.msg import String, Header, Float32
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from math import isnan


class PID:
    def __init__(self, Kp, Td, Ti, dt):
        self.Kp = Kp
        self.Td = Td
        self.Ti = Ti
        self.curr_error = 0
        self.prev_error = 0
        self.sum_error = 0
        self.prev_error_deriv = 0
        self.curr_error_deriv = 0
        self.control = 0
        self.dt = dt

    def update_control(self, current_error, reset_prev=False):
        self.prev_error = self.curr_error
        self.curr_error = current_error
        self.prev_error_deriv = self.curr_error_deriv
        self.curr_error_deriv = (self.curr_error - self.prev_error) / self.dt
        self.sum_error = self.sum_error + self.curr_error

        self.control = self.Kp  self.curr_error + self.Td  self.curr_error_deriv + self.Ti * self.sum_error

    def get_control(self):
        return self.control


class WallFollowerHusky:
    def __init__(self):
        rospy.init_node('wall_follower_husky', anonymous=True)

        self.forward_speed = rospy.get_param("~forward_speed")
        self.desired_distance_from_wall = rospy.get_param("~desired_distance_from_wall")
        self.hz = 50

        # using geometry_msgs.Twist messages
        self.cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)

        # this will set up a callback function that gets executed
        # upon each spinOnce() call, as long as a laser scan
        # message has been published in the meantime by another node
        self.laser_sub = rospy.Subscriber("/scan", LaserScan, self.laser_scan_callback)
        self.cte_pub = rospy.Publisher('/husky_1/cte', Float32, queue_size=1)

        self.pid_controller = PID(0.16, 0.61, 0., 1. / self.hz)
        
    def laser_scan_callback(self, msg):
        # Populate this command based on the distance to the closest
        # object in laser scan. I.e. compute the cross-track error
        # as mentioned in the PID slides.
        # current_error = min(filter(lambda x: not isnan(x), msg.ranges)) - self.desired_distance_from_wall
        
 	for i in range(len(msg.ranges)/2):
       		if msg.ranges[i] < distance_from_wall:
       			distance_from_wall = msg.ranges[i]
	#Calculating the cross track error
       	cross_track_error = self.desired_distance_from_wall - distance_from_wall
	self.cte_pub.publish(current_error)

        # You can populate the command based on either of the following two methods:
        # (1) using only the distance to the closest wall
        # (2) using the distance to the closest wall and the orientation of the wall
        #
        # If you select option 2, you might want to use cascading PID control.
        self.pid_controller.update_control(current_error)
        twist = Twist()
        twist.linear.x = twist.linear.y = twist.linear.z = self.forward_speed
        twist.angular.z = self.pid_controller.get_control()
        self.cmd_pub.publish(twist)

    def configure_callback(self, config, level):
        self.pid_controller.Kp = config['Kp']
        self.pid_controller.Td = config['Td']
        self.pid_controller.Ti = config['Ti']
        return config

    def run(self):
        rate = rospy.Rate(self.hz)
        while not rospy.is_shutdown():
            rate.sleep()


if _name_ == '__main__':
    wfh = WallFollowerHusky()
    wfh.run()