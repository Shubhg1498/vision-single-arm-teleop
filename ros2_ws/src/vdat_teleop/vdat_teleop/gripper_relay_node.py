import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class GripperRelayNode(Node):
    def __init__(self):
        super().__init__("gripper_relay_node")

        self.declare_parameter("input_topic", "/teleop/right_gripper/close")
        self.declare_parameter("output_topic", "/panda_hand_controller/joint_trajectory")
        self.declare_parameter("open_position", 0.04)
        self.declare_parameter("closed_position", 0.0)
        self.declare_parameter("motion_time_sec", 0.4)

        self.input_topic = self.get_parameter("input_topic").value
        self.output_topic = self.get_parameter("output_topic").value
        self.open_position = float(self.get_parameter("open_position").value)
        self.closed_position = float(self.get_parameter("closed_position").value)
        self.motion_time_sec = float(self.get_parameter("motion_time_sec").value)

        self.last_state = None

        self.sub = self.create_subscription(
            Bool,
            self.input_topic,
            self.callback,
            10,
        )

        self.pub = self.create_publisher(
            JointTrajectory,
            self.output_topic,
            10,
        )

        self.get_logger().info("Gripper relay node started.")
        self.get_logger().info(f"Input topic:  {self.input_topic}")
        self.get_logger().info(f"Output topic: {self.output_topic}")

    def callback(self, msg: Bool):
        close_gripper = bool(msg.data)

        # Avoid continuously sending same command
        if self.last_state == close_gripper:
            return

        self.last_state = close_gripper

        if close_gripper:
            position = self.closed_position
            self.get_logger().info("Closing Panda gripper.")
        else:
            position = self.open_position
            self.get_logger().info("Opening Panda gripper.")

        traj = JointTrajectory()
        traj.header.stamp = self.get_clock().now().to_msg()
        traj.joint_names = [
            "panda_finger_joint1",
            "panda_finger_joint2",
        ]

        point = JointTrajectoryPoint()
        point.positions = [
            position,
            position,
        ]
        point.time_from_start.sec = int(self.motion_time_sec)
        point.time_from_start.nanosec = int(
            (self.motion_time_sec - int(self.motion_time_sec)) * 1e9
        )

        traj.points.append(point)
        self.pub.publish(traj)


def main():
    rclpy.init()
    node = GripperRelayNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
