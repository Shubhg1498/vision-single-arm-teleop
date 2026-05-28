import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TwistStamped


class ServoTwistRelayNode(Node):
    def __init__(self):
        super().__init__("servo_twist_relay_node")

        self.declare_parameter("input_topic", "/teleop/right_arm/twist_cmd")
        self.declare_parameter("output_topic", "/servo_node/delta_twist_cmds")
        self.declare_parameter("servo_frame_id", "panda_link0")

        self.declare_parameter("publish_rate_hz", 30.0)
        self.declare_parameter("scale", 0.35)

        # Safety / robustness parameters
        self.declare_parameter("command_timeout_sec", 0.25)
        self.declare_parameter("max_linear_speed", 0.08)
        self.declare_parameter("max_linear_accel", 0.25)
        self.declare_parameter("smoothing_alpha", 0.25)

        self.input_topic = self.get_parameter("input_topic").value
        self.output_topic = self.get_parameter("output_topic").value
        self.servo_frame_id = self.get_parameter("servo_frame_id").value

        self.publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self.scale = float(self.get_parameter("scale").value)

        self.command_timeout_sec = float(self.get_parameter("command_timeout_sec").value)
        self.max_linear_speed = float(self.get_parameter("max_linear_speed").value)
        self.max_linear_accel = float(self.get_parameter("max_linear_accel").value)
        self.smoothing_alpha = float(self.get_parameter("smoothing_alpha").value)

        self.raw_vx = 0.0
        self.raw_vy = 0.0
        self.raw_vz = 0.0

        self.smooth_vx = 0.0
        self.smooth_vy = 0.0
        self.smooth_vz = 0.0

        self.last_input_time = self.get_clock().now()
        self.last_publish_time = self.get_clock().now()

        self.sub = self.create_subscription(
            TwistStamped,
            self.input_topic,
            self.callback,
            10,
        )

        self.pub = self.create_publisher(
            TwistStamped,
            self.output_topic,
            10,
        )

        timer_period = 1.0 / self.publish_rate_hz
        self.timer = self.create_timer(timer_period, self.publish_smoothed_command)

        self.get_logger().info("Robust Servo twist relay started.")
        self.get_logger().info(f"Input topic:        {self.input_topic}")
        self.get_logger().info(f"Output topic:       {self.output_topic}")
        self.get_logger().info(f"Servo frame:        {self.servo_frame_id}")
        self.get_logger().info(f"Scale:              {self.scale}")
        self.get_logger().info(f"Max speed:          {self.max_linear_speed}")
        self.get_logger().info(f"Max accel:          {self.max_linear_accel}")
        self.get_logger().info(f"Timeout:            {self.command_timeout_sec}")
        self.get_logger().info(f"Smoothing alpha:    {self.smoothing_alpha}")

    @staticmethod
    def clamp(value, lower, upper):
        return max(lower, min(upper, value))

    def limit_speed_vector(self, vx, vy, vz):
        speed = math.sqrt(vx * vx + vy * vy + vz * vz)

        if speed <= self.max_linear_speed or speed < 1e-6:
            return vx, vy, vz

        scale = self.max_linear_speed / speed
        return vx * scale, vy * scale, vz * scale

    def limit_acceleration(self, target, current, dt):
        max_delta = self.max_linear_accel * dt
        delta = target - current
        delta = self.clamp(delta, -max_delta, max_delta)
        return current + delta

    def callback(self, msg: TwistStamped):
        self.raw_vx = msg.twist.linear.x * self.scale
        self.raw_vy = msg.twist.linear.y * self.scale
        self.raw_vz = msg.twist.linear.z * self.scale

        self.raw_vx, self.raw_vy, self.raw_vz = self.limit_speed_vector(
            self.raw_vx,
            self.raw_vy,
            self.raw_vz,
        )

        self.last_input_time = self.get_clock().now()

    def publish_smoothed_command(self):
        now = self.get_clock().now()

        dt = (now - self.last_publish_time).nanoseconds * 1e-9
        self.last_publish_time = now

        if dt <= 0.0:
            dt = 1.0 / self.publish_rate_hz

        time_since_input = (now - self.last_input_time).nanoseconds * 1e-9

        # Deadman behavior: if webcam commands stop, publish zero velocity
        if time_since_input > self.command_timeout_sec:
            target_vx = 0.0
            target_vy = 0.0
            target_vz = 0.0
        else:
            target_vx = self.raw_vx
            target_vy = self.raw_vy
            target_vz = self.raw_vz

        # Low-pass filter
        target_vx = self.smoothing_alpha * target_vx + (1.0 - self.smoothing_alpha) * self.smooth_vx
        target_vy = self.smoothing_alpha * target_vy + (1.0 - self.smoothing_alpha) * self.smooth_vy
        target_vz = self.smoothing_alpha * target_vz + (1.0 - self.smoothing_alpha) * self.smooth_vz

        # Acceleration limiting
        self.smooth_vx = self.limit_acceleration(target_vx, self.smooth_vx, dt)
        self.smooth_vy = self.limit_acceleration(target_vy, self.smooth_vy, dt)
        self.smooth_vz = self.limit_acceleration(target_vz, self.smooth_vz, dt)

        out = TwistStamped()
        out.header.stamp = now.to_msg()
        out.header.frame_id = self.servo_frame_id

        out.twist.linear.x = self.smooth_vx
        out.twist.linear.y = self.smooth_vy
        out.twist.linear.z = self.smooth_vz

        out.twist.angular.x = 0.0
        out.twist.angular.y = 0.0
        out.twist.angular.z = 0.0

        self.pub.publish(out)


def main():
    rclpy.init()
    node = ServoTwistRelayNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()