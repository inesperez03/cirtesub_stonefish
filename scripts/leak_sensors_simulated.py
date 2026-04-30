#!/usr/bin/env python3

from __future__ import annotations

from rclpy.node import Node
import rclpy
from sura_msgs.msg import LeakSensor


class LeakSensorsSimulated(Node):
    def __init__(self) -> None:
        super().__init__("leak_sensors_simulated")

        self.declare_parameter("leak_topic", "/cirtesub/leak_sensors")
        self.declare_parameter("publish_period", 1.0)
        self.declare_parameter(
            "sensor_frames",
            ["cirtesub/main_cylinder", "cirtesub/battery_cylinder"],
        )
        self.declare_parameter("leak_detected", [False, False])
        for index, _frame in enumerate(self._sensor_frames()):
            self.declare_parameter(f"leak_detected_{index}", False)

        self._leak_topic = str(self.get_parameter("leak_topic").value)
        self._publish_period = float(self.get_parameter("publish_period").value)

        self._leak_pub = self.create_publisher(LeakSensor, self._leak_topic, 10)
        self._timer = self.create_timer(self._publish_period, self._publish_leaks)

    def _publish_leaks(self) -> None:
        now = self.get_clock().now().to_msg()
        frames = self._sensor_frames()
        leak_values = self._leak_values()

        for index, frame in enumerate(frames):
            msg = LeakSensor()
            msg.header.stamp = now
            msg.header.frame_id = frame
            msg.frame_id = frame
            msg.leak_detected = leak_values[index] if index < len(leak_values) else False
            self._leak_pub.publish(msg)

    def _sensor_frames(self) -> list[str]:
        values = self.get_parameter("sensor_frames").get_parameter_value()
        frames = [str(frame) for frame in values.string_array_value]
        if not frames:
            return ["cirtesub/main_cylinder"]
        return frames

    def _leak_values(self) -> list[bool]:
        values = self.get_parameter("leak_detected").get_parameter_value()
        leak_values = [bool(value) for value in values.bool_array_value]
        frames = self._sensor_frames()
        while len(leak_values) < len(frames):
            leak_values.append(False)

        for index, _frame in enumerate(frames):
            parameter_name = f"leak_detected_{index}"
            if self.has_parameter(parameter_name):
                leak_values[index] = bool(self.get_parameter(parameter_name).value)
        return leak_values


def main() -> None:
    rclpy.init()
    node = LeakSensorsSimulated()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
