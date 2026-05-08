#!/usr/bin/env python3
import rospy
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
import time

rospy.init_node('fake_path_publisher', anonymous=True)
pub = rospy.Publisher('/path', Path, queue_size=10)
time.sleep(2)
print('basliyor...')
rate = rospy.Rate(1)

while not rospy.is_shutdown():
    path = Path()
    path.header.stamp = rospy.Time.now()
    path.header.frame_id = 'map'
    pose = PoseStamped()
    pose.pose.position.x = 5.0
    pose.pose.position.y = 5.0
    path.poses.append(pose)
    pub.publish(path)
    print('yayinlandi!')
    rate.sleep()