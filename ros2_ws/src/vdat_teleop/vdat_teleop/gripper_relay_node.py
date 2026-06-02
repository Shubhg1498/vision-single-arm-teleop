import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from control_msgs.action import GripperCommand
from std_msgs.msg import Bool
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class GripperRelayNode(Node):
    def __init__(self):
        super().__init__("gripper_relay_node")

        self.declare_parameter("input_topic", "/teleop/right_gripper/close")
        self.declare_parameter("command_type", "action")
        self.declare_parameter(
            "output_action_topic", "/panda_hand_controller/gripper_cmd"
        )
        self.declare_parameter(
            "output_topic", "/panda_hand_controller/joint_trajectory"
        )
        self.declare_parameter("open_position", 0.04)
        self.declare_parameter("closed_position", 0.0)
        self.declare_parameter("max_effort", 20.0)
        self.declare_parameter("motion_time_sec", 0.4)

        self.input_topic = self.get_parameter("input_topic").value
        self.command_type = self.get_parameter("command_type").value
        self.output_action_topic = self.get_parameter("output_action_topic").value
        self.output_topic = self.get_parameter("output_topic").value
        self.open_position = float(self.get_parameter("open_position").value)
        self.closed_position = float(self.get_parameter("closed_position").value)
        self.max_effort = float(self.get_parameter("max_effort").value)
        self.motion_time_sec = float(self.get_parameter("motion_time_sec").value)

        self.last_state = None
        self.action_client = None
        self.pub = None

        self.sub = self.create_subscription(
            Bool,
            self.input_topic,
            self.callback,
            10,
        )

        if self.command_type == "action":
            self.action_client = ActionClient(
                self, GripperCommand, self.output_action_topic
            )
        else:
            self.pub = self.create_publisher(
                JointTrajectory,
                self.output_topic,
                10,
            )

        self.get_logger().info("Gripper relay node started.")
        self.get_logger().info(f"Input topic:  {self.input_topic}")
        if self.command_type == "action":
            self.get_logger().info(f"Action topic: {self.output_action_topic}")
        else:
            self.get_logger().info(f"Output topic: {self.output_topic}")

    def callback(self, msg: Bool):
        close_gripper = bool(msg.data)

        if self.last_state == close_gripper:
            return

        self.last_state = close_gripper
        position = self.closed_position if close_gripper else self.open_position

        if close_gripper:
            self.get_logger().info("Closing Panda gripper.")
        else:
            self.get_logger().info("Opening Panda gripper.")

        if self.command_type == "action":
            self._send_action(position)
        else:
            self._send_trajectory(position)

    def _send_action(self, position: float):
        if not self.action_client.server_is_ready():
            self.get_logger().warning(
                f"Gripper action server not ready: {self.output_action_topic}"
            )
            return

        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = self.max_effort
        self.action_client.send_goal_async(goal)

    def _send_trajectory(self, position: float):
        traj = JointTrajectory()
        traj.header.stamp = self.get_clock().now().to_msg()
        traj.joint_names = [
            "panda_finger_joint1",
            "panda_finger_joint2",
        ]

        point = JointTrajectoryPoint()
        point.positions = [position, position]
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
