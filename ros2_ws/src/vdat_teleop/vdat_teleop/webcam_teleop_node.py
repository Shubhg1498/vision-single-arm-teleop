import cv2
import platform

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Bool

from vision_dual_arm_teleop.tracking.hand_tracker import HandTracker
from vision_dual_arm_teleop.mapping.hand_to_twist import HandToTwistMapper


def draw_command_overlay(
    frame, cmd=None, gripper_close=False, depth_mode_text="",
    arm_frozen=False, gripper_latched=False,
):
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
        end_x = int(center[0] - cmd.vy * arrow_scale)
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
            (20, h - 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )
    else:
        cv2.putText(
            frame,
            "cmd vx=+0.00 vy=+0.00 vz=+0.00",
            (20, h - 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

    gripper_text = "GRIPPER: CLOSE" if gripper_close else "GRIPPER: OPEN"
    if gripper_latched:
        gripper_text += " (latched)"
    gripper_color = (0, 0, 255) if gripper_close else (0, 255, 0)

    if arm_frozen:
        cv2.putText(
            frame,
            "ARM XY FROZEN (pinch)",
            (20, h - 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 165, 255),
            2,
        )

    cv2.putText(
        frame,
        gripper_text,
        (20, h - 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        gripper_color,
        2,
    )

    cv2.putText(
        frame,
        depth_mode_text,
        (20, h - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 0),
        2,
    )

    cv2.putText(
        frame,
        "Pinch=freeze | Open hand=move | Pinch=close | C=transport latch | W/S=depth",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (255, 255, 0),
        2,
    )

    return frame


def open_camera(camera_index: int, camera_device: str = ""):
    """Open a V4L2 camera by /dev/video path or numeric index."""
    backend = cv2.CAP_V4L2 if platform.system() == "Linux" else cv2.CAP_ANY
    source = camera_device.strip() if camera_device.strip() else int(camera_index)
    cap = cv2.VideoCapture(source, backend)
    if not cap.isOpened() and camera_device.strip():
        cap = cv2.VideoCapture(source)
    return cap, source


class WebcamTeleopNode(Node):
    def __init__(self):
        super().__init__("webcam_teleop_node")

        self.declare_parameter("camera_index", 0)
        self.declare_parameter("camera_device", "")
        self.declare_parameter("flip_horizontal", True)
        self.declare_parameter("publish_rate_hz", 30.0)
        self.declare_parameter("depth_speed", 0.12)

        self.camera_index = int(self.get_parameter("camera_index").value)
        self.camera_device = str(self.get_parameter("camera_device").value)
        self.flip_horizontal = bool(self.get_parameter("flip_horizontal").value)
        self.publish_rate_hz = self.get_parameter("publish_rate_hz").value
        self.depth_speed = self.get_parameter("depth_speed").value

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

        self.cap, camera_source = open_camera(self.camera_index, self.camera_device)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open camera (index={self.camera_index}, "
                f"device={self.camera_device!r})"
            )

        self.tracker = HandTracker()
        self.mapper = HandToTwistMapper()

        self.depth_vx = 0.0
        self.depth_mode_text = "Depth: STOP"
        self.was_pinching = False
        self.gripper_latched = False

        timer_period = 1.0 / self.publish_rate_hz
        self.timer = self.create_timer(timer_period, self.on_timer)

        self.get_logger().info("Webcam teleop node started.")
        self.get_logger().info(f"Camera source: {camera_source}")
        self.get_logger().info(f"Flip horizontal: {self.flip_horizontal}")
        self.get_logger().info("Publishing:")
        self.get_logger().info("  /teleop/right_arm/twist_cmd")
        self.get_logger().info("  /teleop/right_gripper/close")
        self.get_logger().info("Keyboard depth control:")
        self.get_logger().info("  W = forward")
        self.get_logger().info("  S = backward")
        self.get_logger().info("  release/no key = stop depth")

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

    def read_keyboard_depth_command(self):
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            self.get_logger().info("Quit requested from OpenCV window.")
            rclpy.shutdown()
            return

        if key == ord("w"):
            self.depth_vx = self.depth_speed
            self.depth_mode_text = "Depth: FORWARD"
        elif key == ord("s"):
            self.depth_vx = -self.depth_speed
            self.depth_mode_text = "Depth: BACKWARD"
        elif key == ord("c"):
            self.gripper_latched = not self.gripper_latched
            state = "LATCHED (hold object)" if self.gripper_latched else "UNLATCHED"
            self.get_logger().info(f"Gripper transport latch: {state}")
        else:
            self.depth_vx = 0.0
            self.depth_mode_text = "Depth: STOP"

    def on_timer(self):
        ok, frame = self.cap.read()

        if not ok:
            self.get_logger().warn("Could not read frame. Publishing stop.")
            self.publish_stop()
            return

        frame = cv2.flip(frame, 1) if self.flip_horizontal else frame
        observations, results = self.tracker.process(frame)

        if "Right" not in observations:
            self.publish_stop()

            frame = self.tracker.draw(frame, results, observations)
            frame = draw_command_overlay(frame, None, False, "Depth: STOP")

            cv2.putText(
                frame,
                "Right hand not detected - STOP",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

            cv2.imshow("ROS2 Webcam Teleop", frame)
            self.read_keyboard_depth_command()
            return

        obs = observations["Right"]
        is_pinching = obs.gesture.is_pinching

        if is_pinching != self.was_pinching:
            self.mapper.reset(obs.wrist_xy)
        self.was_pinching = is_pinching

        cmd = self.mapper.map(obs.wrist_xy, is_pinching)

        # Pinch freezes all hand-driven motion so you can enter the frame safely.
        if is_pinching:
            cmd.vy = 0.0
            cmd.vz = 0.0
            cmd.vx = 0.0
        else:
            cmd.vx = self.depth_vx

        gripper_close = is_pinching or self.gripper_latched
        cmd.gripper_close = gripper_close

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
        frame = draw_command_overlay(
            frame,
            cmd,
            gripper_close,
            self.depth_mode_text,
            arm_frozen=is_pinching,
            gripper_latched=self.gripper_latched,
        )

        cv2.imshow("ROS2 Webcam Teleop", frame)
        self.read_keyboard_depth_command()

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
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()
        else:
            node.destroy_node()


if __name__ == "__main__":
    main()