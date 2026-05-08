#!/usr/bin/env python3
import rospy
import math
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist
from nav_msgs.msg import Path, Odometry
import tf

class PIDController:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.prev_error = 0.0
        self.integral = 0.0

    def compute(self, target, current, dt):
        error = target - current
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        self.prev_error = error
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        return output, error

class ControlNode:
    def __init__(self):
        rospy.init_node('pid_control_node', anonymous=True)

        # PID parametreleri
        self.steering_pid = PIDController(Kp=1.0, Ki=0.0, Kd=0.1)
        self.speed_pid    = PIDController(Kp=1.0, Ki=0.0, Kd=0.1)

        # Mevcut değerler
        self.current_steering = 0.0
        self.current_speed    = 0.0

        # Araçın mevcut pozisyonu
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        # Hedef değerler
        self.target_steering = 0.0
        self.target_speed    = 1.0  # m/s (Gazebo için düşük tut)

        # Path'ten gelen hedef nokta
        self.target_x = 0.0
        self.target_y = 0.0
        self.has_path = False

        # Subscriber'lar
        rospy.Subscriber('/beemobs/FeedbackSteeringAngle', Float32, self.steering_cb)
        rospy.Subscriber('/beemobs/FB_VehicleSpeed', Float32, self.speed_cb)
        rospy.Subscriber('/path', Path, self.path_cb)
        rospy.Subscriber('/odom', Odometry, self.odom_cb)  # YENİ!

        # Publisher'lar
        self.steering_pub = rospy.Publisher('/beemobs/steering_target_value', Float32, queue_size=10)
        self.speed_pub = rospy.Publisher('/beemobs/speed_target_value', Float32, queue_size=10)
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)

        self.last_time = rospy.Time.now()
        rospy.loginfo("PID Control Node başladı!")

    def steering_cb(self, msg):
        self.current_steering = msg.data

    def speed_cb(self, msg):
        self.current_speed = msg.data

    def odom_cb(self, msg):
        # Gazebo'dan konum al
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        # Quaternion → yaw
        orientation = msg.pose.pose.orientation
        _, _, self.current_yaw = tf.transformations.euler_from_quaternion(
            [orientation.x, orientation.y, orientation.z, orientation.w]
        )

    def path_cb(self, msg):
        if len(msg.poses) > 0:
            self.target_x = msg.poses[0].pose.position.x
            self.target_y = msg.poses[0].pose.position.y
            self.has_path = True
            rospy.loginfo(f"Yeni hedef nokta: x={self.target_x:.2f} y={self.target_y:.2f}")

    def compute_steering_angle(self):
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y

        angle_to_target = math.atan2(dy, dx)
        steering_angle = angle_to_target - self.current_yaw

        # -pi ile +pi arasında tut
        steering_angle = math.atan2(
            math.sin(steering_angle),
            math.cos(steering_angle)
        )

        return math.degrees(steering_angle)

    def run(self):
        rate = rospy.Rate(10)

        while not rospy.is_shutdown():
            now = rospy.Time.now()
            dt = (now - self.last_time).to_sec()
            self.last_time = now

            if dt <= 0:
                rate.sleep()
                continue

            if self.has_path:
                self.target_steering = self.compute_steering_angle()

                # Hedefe ulaştık mı?
                dx = self.target_x - self.current_x
                dy = self.target_y - self.current_y
                distance = math.sqrt(dx**2 + dy**2)

                if distance < 0.5:  # 0.5 metre yaklaşınca dur
                    rospy.loginfo("Hedefe ulaşıldı! Duruyorum.")
                    cmd = Twist()
                    self.cmd_vel_pub.publish(cmd)
                    self.has_path = False  # path'i sıfırla
                    rate.sleep()
                    continue

            # PID hesapla
            steering_out, steering_err = self.steering_pid.compute(
                self.target_steering, self.current_steering, dt)
            speed_out, speed_err = self.speed_pid.compute(
                self.target_speed, self.current_speed, dt)

            # Beemobs topic'lerine yaz
            self.steering_pub.publish(Float32(data=steering_out))
            self.speed_pub.publish(Float32(data=speed_out))

            # cmd_vel yaz
            cmd = Twist()
            cmd.linear.x  = self.target_speed
            cmd.angular.z = math.radians(steering_out)
            self.cmd_vel_pub.publish(cmd)

            rospy.loginfo(
                f"Pos:({self.current_x:.1f},{self.current_y:.1f}) | "
                f"Hedef açı:{self.target_steering:.2f}° | "
                f"Steering hata:{steering_err:.2f} çıkış:{steering_out:.2f} | "
                f"Hız:{self.current_speed:.2f}"
            )

            rate.sleep()

if __name__ == '__main__':
    try:
        node = ControlNode()
        node.run()
    except rospy.ROSInterruptException:
        pass