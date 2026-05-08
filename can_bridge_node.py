#!/usr/bin/env python3
"""
============================================================
CAN BRIDGE NODE
Gazebo testi ve gerçek araç için tek kod.

SIMULATION = True  → Gazebo'da test
SIMULATION = False → Gerçek araçta CAN0'dan okur

DÜZENLEMEN GEREKEN YERLER:
  !! ile işaretli
============================================================
"""

import rospy
import math
import threading
import time
from std_msgs.msg import Float32
from nav_msgs.msg import Odometry
import tf
import sys
print("Script başladı!", flush=True)
sys.stdout.flush()

# ============================================================
# !! BURADAN DÜZENLE
# ============================================================

SIMULATION = True       # Gazebo → True | Gerçek araç → False

# CAN ayarları (SIMULATION=False iken kullanılır)
CAN_INTERFACE = 'can0'  # !! Gerçek araçta can0
CAN_BITRATE   = 500000  # !! Aracına göre değiştir

# !! CAN ID'leri - gerçek araçta doldur
POT_CAN_ID        = 0x201
HIZ_CAN_ID        = 0x202
DIREKSIYON_CAN_ID = 0x203

# Potansiyometre ayarları
POT_MIN = 0
POT_MAX = 4095

# Simülasyon ayarları
SIM_HIZ_MAX = 2.0

# ============================================================

class CANBridge:
    def __init__(self):
        rospy.init_node('can_bridge_node', anonymous=False)
        rospy.loginfo("CAN Bridge başlatılıyor... Mod: {}".format(
            "SİMÜLASYON" if SIMULATION else "GERÇEK ARAÇ"
        ))

        self.gercek_hiz     = 0.0
        self.sim_direksiyon = 0.0
        self.pot_ham        = 0
        self.pot_yuzde      = 0.0

        # Publisher'lar - PID node bunları dinliyor
        self.pub_hiz        = rospy.Publisher('/beemobs/FB_VehicleSpeed',
                                              Float32, queue_size=10)
        self.pub_direksiyon = rospy.Publisher('/beemobs/FeedbackSteeringAngle',
                                              Float32, queue_size=10)
        self.pub_pot_ham    = rospy.Publisher('/arac/pot_ham',
                                              Float32, queue_size=10)
        self.pub_pot_yuzde  = rospy.Publisher('/arac/pot_yuzde',
                                              Float32, queue_size=10)

        if SIMULATION:
            rospy.Subscriber('/odom', Odometry, self.cb_odom)
            rospy.loginfo("Simülasyon: /odom dinleniyor")
            self._sim_loop()
        else:
            if not self._can_baslat():
                rospy.logerr("CAN başlatılamadı!")
                return
            self._can_oku()

        rospy.spin()

    # ---- SİMÜLASYON ----

    def cb_odom(self, msg: Odometry):
        self.gercek_hiz = msg.twist.twist.linear.x
        orientation = msg.pose.pose.orientation
        _, _, yaw = tf.transformations.euler_from_quaternion([
            orientation.x, orientation.y,
            orientation.z, orientation.w
        ])
        self.sim_direksiyon = math.degrees(yaw)

    def _sim_loop(self):
        rate = rospy.Rate(10)
        rospy.loginfo("Simülasyon döngüsü başladı!")

        while not rospy.is_shutdown():
            # Hız ve direksiyon publish et
            self.pub_hiz.publish(Float32(data=self.gercek_hiz))
            self.pub_direksiyon.publish(Float32(data=self.sim_direksiyon))

            # Fake pot - hıza göre üretiliyor
            # Gerçek araçta CAN'dan gelecek
            self.pot_ham   = int(self.gercek_hiz / SIM_HIZ_MAX * POT_MAX)
            self.pot_yuzde = max(0.0, min(100.0,
                                self.gercek_hiz / SIM_HIZ_MAX * 100.0))

            self.pub_pot_ham.publish(Float32(data=float(self.pot_ham)))
            self.pub_pot_yuzde.publish(Float32(data=self.pot_yuzde))

            rospy.loginfo_throttle(2.0,
                f"Hız: {self.gercek_hiz:.2f} m/s | "
                f"Direksiyon: {self.sim_direksiyon:.2f}° | "
                f"Pot: {self.pot_yuzde:.1f}%"
            )
            rate.sleep()

    # ---- GERÇEK ARAÇ ----

    def _can_baslat(self) -> bool:
        try:
            import subprocess
            subprocess.run(['sudo', 'ip', 'link', 'set', 'down', CAN_INTERFACE],
                           capture_output=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', CAN_INTERFACE,
                            'type', 'can', 'bitrate', str(CAN_BITRATE)],
                           capture_output=True, check=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', 'up', CAN_INTERFACE],
                           capture_output=True, check=True)
            import can
            self.bus = can.interface.Bus(channel=CAN_INTERFACE, bustype='socketcan')
            rospy.loginfo(f"CAN OK: {CAN_INTERFACE} @ {CAN_BITRATE}bps")
            return True
        except Exception as e:
            rospy.logerr(f"CAN hatası: {e}")
            return False

    def _can_oku(self):
        import can
        rospy.loginfo("CAN okuma başladı!")

        while not rospy.is_shutdown():
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg is None:
                    continue

                cid = msg.arbitration_id

                # Potansiyometre
                if cid == POT_CAN_ID:
                    raw = int.from_bytes(msg.data[0:2],
                                         byteorder='little', signed=False)
                    pct = (raw - POT_MIN) / (POT_MAX - POT_MIN) * 100.0
                    pct = max(0.0, min(100.0, pct))
                    self.pub_pot_ham.publish(Float32(data=float(raw)))
                    self.pub_pot_yuzde.publish(Float32(data=pct))
                    rospy.loginfo_throttle(1.0, f"Pot: {raw} | {pct:.1f}%")

                # Hız !! parse mantığını düzenle
                elif cid == HIZ_CAN_ID:
                    raw = int.from_bytes(msg.data[0:2], byteorder='little')
                    hiz = raw * 0.1
                    self.pub_hiz.publish(Float32(data=hiz))

                # Direksiyon !! parse mantığını düzenle
                elif cid == DIREKSIYON_CAN_ID:
                    raw = int.from_bytes(msg.data[0:2],
                                          byteorder='little', signed=True)
                    aci = raw * 0.1
                    self.pub_direksiyon.publish(Float32(data=aci))

            except Exception as e:
                rospy.logwarn(f"CAN okuma hatası: {e}")


if __name__ == '__main__':
    try:
        CANBridge()
    except rospy.ROSInterruptException:
        pass