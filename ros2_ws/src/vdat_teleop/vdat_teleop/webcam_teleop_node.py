import cv2

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Bool

from vision_dual_arm_teleop.tracking.hand_tracker import HandTracker
from vision_dual_arm_teleop.mapping.hand_to_twist import HandToTwistMapper


def draw_command_overlay(frame, cmd=None, gripper_close=False):
    h, w, _ = frame.shape

    center = (w // 2, h // 2)
    box_size = 140

    # Draw deadband/control box
    top_left = (center[0] - box_size // 2, center[1] - box_size // 2)
    bottom_right = (center[0] + box_size // 2, center[1] + box_size // 2)

    cv2.rectangle(frame, top_left, bottom_right, (180, 180, 180), 2)
    cv2.circle(frame, center, 5, (255, 255, 255), -1)

    if cmd is not None:
        arrow_scale = 350

        # vy controls left/right image direction
        # vz controls up/down image direction
        end_x = int(center[0] + cmd.vy * arrow_scale)
        end_y = int(center[1] - cmd.vz * arrow_scale)

        cv2.arrowedLine(
            frame,
            center,
            (end_x, end_y),
            (0, 255, 0),
            4,
            tipLength=0.25,
        )

        cv2.putText(
            frame,
            f"cmd vx={cmd.vx:+.2f} vy={cmd.vy:+.2f} vz={cmd.vz:+.2f}",
            (20, h - 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )
    else:
        cv2.putText(
            frame,
            "cmd vx=+0.00 vy=+0.00 vz=+0.00",
            (20, h - 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

    gripper_text = "GRIPPER: CLOSE" if gripper_close else "GRIPPER: OPEN"
    gripper_color = (0, 0, 255) if gripper_close else (0, 255, 0)

    cv2.putText(
        frame,
        gripper_text,
        (20, h - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        gripper_color,
        2,
    )

    return frame


class WebcamTeleopNode(Node):
    def __init__(self):
        super().__init__("webcam_teleop_node")

        self.declare_parameter("camera_index", 0)
        self.declare_parameter("publish_rate_hz", 30.0)

        self.camera_index = self.get_parameter("camera_index").value
        self.publish_rate_hz = self.get_parameter("publish_rate_hz").value

        self.right_twist_pub = self.create_publisher(
            TwistStamped,
            "/teleop/right_arm/twist_cmd",
            10,
        )

        self.right_gripper_pub = self.create_publisher(
            Bool,
            "/teleop/right_gripper/close",
            10,
        )

        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera index {self.camera_index}")

        self.tracker = HandTracker()
        self.mapper = HandToTwistMapper()

        timer_period = 1.0 / self.publish_rate_hz
        self.timer = self.create_timer(timer_period, self.on_timer)

        self.get_logger().info("Webcam teleop node started.")
        self.get_logger().info("Publishing:")
        self.get_logger().info("  /teleop/right_arm/twist_cmd")
        self.get_logger().info("  /teleop/right_gripper/close")

    def publish_stop(self):
        twist_msg = TwistStamped()
        twist_msg.header.stamp = self.get_clock().now().to_msg()
        twist_msg.header.frame_id = "base_link"

        twist_msg.twist.linear.x = 0.0
        twist_msg.twist.linear.y = 0.0
        twist_msg.twist.linear.z = 0.0

        twist_msg.twist.angular.x = 0.0
        twist_msg.twist.angular.y = 0.0
        twist_msg.twist.angular.z = 0.0

        self.right_twist_pub.publish(twist_msg)
        self.right_gripper_pub.publish(Bool(data=False))

    def on_timer(self):
        ok, frame = self.cap.read()

        if not ok:
            self.get_logger().warn("Could not read frame. Publishing stop.")
            self.publish_stop()
            return

        frame = cv2.flip(frame, 1)
        observations, results = self.tracker.process(frame)

        if "Right" not in observations:
            self.publish_stop()

            frame = self.tracker.draw(frame, results, observations)
            frame = draw_command_overlay(frame, None, False)

            cv2.putText(
                frame,
                "Right hand not detected - STOP",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

            cv2.imshow("ROS2 Webcam Teleop", frame)
            cv2.waitKey(1)
            return

        obs = observations["Right"]
        cmd = self.mapper.map(obs.wrist_xy, obs.gesture.is_pinching)

        twist_msg = TwistStamped()
        twist_msg.header.stamp = self.get_clock().now().to_msg()
        twist_msg.header.frame_id = "base_link"

        twist_msg.twist.linear.x = cmd.vx
        twist_msg.twist.linear.y = cmd.vy
        twist_msg.twist.linear.z = cmd.vz

        twist_msg.twist.angular.x = 0.0
        twist_msg.twist.angular.y = 0.0
        twist_msg.twist.angular.z = 0.0

        gripper_msg = Bool()
        gripper_msg.data = cmd.gripper_close

        self.right_twist_pub.publish(twist_msg)
        self.right_gripper_pub.publish(gripper_msg)

        frame = self.tracker.draw(frame, results, observations)
        frame = draw_command_overlay(frame, cmd, cmd.gripper_close)

        cv2.imshow("ROS2 Webcam Teleop", frame)
        cv2.waitKey(1)

        self.get_logger().info(
            f"vx={cmd.vx:+.2f}, vy={cmd.vy:+.2f}, vz={cmd.vz:+.2f}, "
            f"gripper_close={cmd.gripper_close}",
            throttle_duration_sec=0.5,
        )

    def destroy_node(self):
        if hasattr(self, "cap") and self.cap is not None:
            self.cap.release()

        cv2.destroyAllWindows()
        super().destroy_node()


def main():
    rclpy.init()
    node = WebcamTeleopNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()