import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TwistStamped


class ServoTwistRelayNode(Node):
    def __init__(self):
        super().__init__("servo_twist_relay_node")

        self.declare_parameter("input_topic", "/teleop/right_arm/twist_cmd")
        self.declare_parameter("output_topic", "/servo_node/delta_twist_cmds")
        self.declare_parameter("servo_frame_id", "panda_link0")
        self.declare_parameter("scale", 0.35)

        self.input_topic = self.get_parameter("input_topic").value
        self.output_topic = self.get_parameter("output_topic").value
        self.servo_frame_id = self.get_parameter("servo_frame_id").value
        self.scale = float(self.get_parameter("scale").value)

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

        self.get_logger().info("Servo twist relay started.")
        self.get_logger().info(f"Input topic:  {self.input_topic}")
        self.get_logger().info(f"Output topic: {self.output_topic}")
        self.get_logger().info(f"Servo frame:  {self.servo_frame_id}")
        self.get_logger().info(f"Scale:        {self.scale}")

    def callback(self, msg: TwistStamped):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self.servo_frame_id

        out.twist.linear.x = msg.twist.linear.x * self.scale
        out.twist.linear.y = msg.twist.linear.y * self.scale
        out.twist.linear.z = msg.twist.linear.z * self.scale

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
