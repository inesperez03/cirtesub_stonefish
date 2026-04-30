#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
import math

from rclpy.node import Node
import rclpy
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Float64MultiArray


@dataclass
class ThrusterTopicState:
    commands: list[float]
    last_update_seconds: float | None = None


class BatteryStatusSimulated(Node):
    def __init__(self) -> None:
        super().__init__("battery_status_simulated")

        self.declare_parameter("battery_topic", "/cirtesub/battery/status")
        self.declare_parameter(
            "thruster_topics",
            ["/cirtesub/controller/thruster_setpoints_sim"],
        )
        self.declare_parameter("publish_period", 1.0)
        self.declare_parameter("nominal_voltage", 22.2)
        self.declare_parameter("voltage_oscillation_amplitude", 0.15)
        self.declare_parameter("voltage_oscillation_period", 12.0)
        self.declare_parameter("cell_count", 6)
        self.declare_parameter("full_cell_voltage", 4.2)
        self.declare_parameter("empty_cell_voltage", 3.2)
        self.declare_parameter("design_capacity_ah", 16.0)
        self.declare_parameter("jetson_current_a", 2.0)
        self.declare_parameter("base_electronics_current_a", 0.5)
        self.declare_parameter("current_per_thruster_unit_a", 8.0)
        self.declare_parameter("max_thruster_command", 1.0)
        self.declare_parameter("stale_thruster_timeout", 2.0)

        self._battery_topic = str(self.get_parameter("battery_topic").value)
        self._publish_period = float(self.get_parameter("publish_period").value)
        self._start_time_seconds = self.get_clock().now().nanoseconds / 1e9

        thruster_topics = [
            str(topic)
            for topic in self.get_parameter("thruster_topics").get_parameter_value().string_array_value
        ]
        if not thruster_topics:
            thruster_topics = ["/cirtesub/controller/thruster_setpoints_sim"]

        self._thrusters = {
            topic: ThrusterTopicState(commands=[])
            for topic in thruster_topics
        }
        self._subscriptions = [
            self.create_subscription(
                Float64MultiArray,
                topic,
                self._make_thruster_callback(topic),
                10,
            )
            for topic in thruster_topics
        ]

        self._battery_pub = self.create_publisher(BatteryState, self._battery_topic, 10)
        self._timer = self.create_timer(self._publish_period, self._publish_battery)

    def _make_thruster_callback(self, topic: str):
        def callback(msg: Float64MultiArray) -> None:
            state = self._thrusters[topic]
            state.commands = list(msg.data)
            state.last_update_seconds = self.get_clock().now().nanoseconds / 1e9

        return callback

    def _publish_battery(self) -> None:
        now = self.get_clock().now()
        now_seconds = now.nanoseconds / 1e9
        voltage = self._battery_voltage(now_seconds)
        cell_count = max(int(self.get_parameter("cell_count").value), 1)
        cell_voltage = voltage / float(cell_count)
        percentage = self._battery_percentage(cell_voltage)
        design_capacity = float(self.get_parameter("design_capacity_ah").value)

        thruster_current = self._estimate_thruster_current(now_seconds)
        total_current = (
            float(self.get_parameter("jetson_current_a").value)
            + float(self.get_parameter("base_electronics_current_a").value)
            + thruster_current
        )

        msg = BatteryState()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = "cirtesub/battery"
        msg.voltage = voltage
        msg.current = -total_current
        msg.charge = percentage * design_capacity
        msg.capacity = design_capacity
        msg.design_capacity = design_capacity
        msg.percentage = percentage
        msg.present = True
        msg.cell_voltage = [cell_voltage] * cell_count
        msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        msg.power_supply_health = self._battery_health(percentage)
        msg.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LION
        self._battery_pub.publish(msg)

    def _battery_voltage(self, now_seconds: float) -> float:
        nominal_voltage = float(self.get_parameter("nominal_voltage").value)
        amplitude = float(self.get_parameter("voltage_oscillation_amplitude").value)
        period = max(float(self.get_parameter("voltage_oscillation_period").value), 1e-6)
        elapsed = now_seconds - self._start_time_seconds
        return nominal_voltage + amplitude * math.sin(2.0 * math.pi * elapsed / period)

    def _battery_percentage(self, cell_voltage: float) -> float:
        full_cell_voltage = float(self.get_parameter("full_cell_voltage").value)
        empty_cell_voltage = float(self.get_parameter("empty_cell_voltage").value)
        usable_range = max(full_cell_voltage - empty_cell_voltage, 1e-6)
        return max(min((cell_voltage - empty_cell_voltage) / usable_range, 1.0), 0.0)

    def _battery_health(self, percentage: float) -> int:
        if percentage < 0.25:
            return BatteryState.POWER_SUPPLY_HEALTH_DEAD
        return BatteryState.POWER_SUPPLY_HEALTH_GOOD

    def _estimate_thruster_current(self, now_seconds: float) -> float:
        total_normalized_effort = 0.0
        max_thruster_command = max(
            float(self.get_parameter("max_thruster_command").value),
            1e-6,
        )
        stale_thruster_timeout = float(
            self.get_parameter("stale_thruster_timeout").value
        )
        for state in self._thrusters.values():
            if state.last_update_seconds is None:
                continue
            if now_seconds - state.last_update_seconds > stale_thruster_timeout:
                continue

            for command in state.commands:
                normalized = min(abs(command) / max_thruster_command, 1.0)
                total_normalized_effort += normalized

        return total_normalized_effort * float(
            self.get_parameter("current_per_thruster_unit_a").value
        )


def main() -> None:
    rclpy.init()
    node = BatteryStatusSimulated()
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
