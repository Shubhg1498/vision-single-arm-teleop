import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Bool


class WebcamTeleopNode(Node):
    """Placeholder ROS2 publisher node.

    Next step:
    Integrate MediaPipe here or bridge from the standalone Python module.
    For now it publishes zero velocity so the ROS2 package builds cleanly.
    """

    def __init__(self):
        super().__init__("webcam_teleop_node")
        self.right_twist_pub = self.create_publisher(TwistStamped, "/teleop/right_arm/twist_cmd", 10)
        self.left_twist_pub = self.create_publisher(TwistStamped, "/teleop/left_arm/twist_cmd", 10)
        self.right_gripper_pub = self.create_publisher(Bool, "/teleop/right_gripper/close", 10)
        self.left_gripper_pub = self.create_publisher(Bool, "/teleop/left_gripper/close", 10)

        self.timer = self.create_timer(0.02, self.on_timer)  # 50 Hz
        self.get_logger().info("Webcam teleop node started. Publishing placeholder commands.")

    def on_timer(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        self.right_twist_pub.publish(msg)
        self.left_twist_pub.publish(msg)
        self.right_gripper_pub.publish(Bool(data=False))
        self.left_gripper_pub.publish(Bool(data=False))


def main():
    rclpy.init()
    node = WebcamTeleopNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
