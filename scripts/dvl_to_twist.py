#!/usr/bin/env python3

from geometry_msgs.msg import TwistWithCovarianceStamped
import rclpy
from rclpy.node import Node
from stonefish_ros2.msg import DVL


class DvlToTwist(Node):
    def __init__(self):
        super().__init__("dvl_to_twist")

        self.declare_parameter("input_topic", "/cirtesub/sensors/dvl")
        self.declare_parameter("output_topic", "/cirtesub/sensors/dvl/twist")
        self.declare_parameter("frame_id", "cirtesub/DVL")
        self.declare_parameter("fallback_velocity_variance", 0.01)
        self.declare_parameter("angular_velocity_variance", 1000000.0)

        input_topic = self.get_parameter("input_topic").value
        output_topic = self.get_parameter("output_topic").value

        self._publisher = self.create_publisher(TwistWithCovarianceStamped, output_topic, 10)
        self.create_subscription(DVL, input_topic, self._dvl_callback, 10)

    def _dvl_callback(self, msg: DVL) -> None:
        twist = TwistWithCovarianceStamped()
        twist.header.stamp = msg.header.stamp
        twist.header.frame_id = str(self.get_parameter("frame_id").value)
        twist.twist.twist.linear = msg.velocity

        covariance = [0.0] * 36
        fallback_variance = float(self.get_parameter("fallback_velocity_variance").value)
        angular_variance = float(self.get_parameter("angular_velocity_variance").value)
        covariance[0] = msg.velocity_covariance[0] if msg.velocity_covariance[0] > 0.0 else fallback_variance
        covariance[7] = msg.velocity_covariance[4] if msg.velocity_covariance[4] > 0.0 else fallback_variance
        covariance[14] = msg.velocity_covariance[8] if msg.velocity_covariance[8] > 0.0 else fallback_variance
        covariance[21] = angular_variance
        covariance[28] = angular_variance
        covariance[35] = angular_variance
        twist.twist.covariance = covariance

        self._publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = DvlToTwist()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
