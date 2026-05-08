#!/bin/bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
roscore &
sleep 5
rosrun control_node can_bridge_node.py
