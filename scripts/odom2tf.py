#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
from rclpy.qos import QoSProfile
from rclpy.time import Time


def qmul(a, b):
    """Hamilton product a ⊗ b. Quaternions as (x, y, z, w)."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def qnorm(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w)
    if n == 0.0:
        return (0.0, 0.0, 0.0, 1.0)
    return (x / n, y / n, z / n, w / n)


class OdomToTf(Node):
    def __init__(self):
        super().__init__("odom_to_tf")
        qos_profile = QoSProfile(depth=10)
        self.subscription = self.create_subscription(
            Odometry, "/cirtesub/odometry", self.callback, qos_profile
        )
        self.br = TransformBroadcaster(self)

        # Corrección fija: roll = pi
        self.q_roll_pi = (1.0, 0.0, 0.0, 0.0)

        # Corrección fija: yaw = -90deg
        s = math.sqrt(0.5)
        self.q_yaw_m90 = (0.0, 0.0, -s, s)

        self.q_total = qnorm(qmul(self.q_yaw_m90, self.q_roll_pi))
        
    def callback(self, msg: Odometry):
        t = TransformStamped()

        t.header.stamp = Time(
            seconds=msg.header.stamp.sec,
            nanoseconds=msg.header.stamp.nanosec
        ).to_msg()

        t.header.frame_id = "world_ned"
        t.child_frame_id = "cirtesub/base_link"

        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z

        q_in = (
            msg.pose.pose.orientation.x,
            msg.pose.pose.orientation.y,
            msg.pose.pose.orientation.z,
            msg.pose.pose.orientation.w,
        )

        q_out = qmul(q_in, self.q_total)
        q_out = qnorm(q_out)

        t.transform.rotation.x = q_out[0]
        t.transform.rotation.y = q_out[1]
        t.transform.rotation.z = q_out[2]
        t.transform.rotation.w = q_out[3]

        self.br.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToTf()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()