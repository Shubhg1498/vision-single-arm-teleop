import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TwistStamped, PoseStamped
from visualization_msgs.msg import Marker


class VirtualEndEffectorSimulator(Node):
    def __init__(self):
        super().__init__("virtual_ee_simulator_node")

        self.declare_parameter("frame_id", "base_link")
        self.declare_parameter("publish_rate_hz", 30.0)

        self.frame_id = self.get_parameter("frame_id").value
        self.publish_rate_hz = self.get_parameter("publish_rate_hz").value

        self.pose_pub = self.create_publisher(
            PoseStamped,
            "/teleop/right_arm/ee_pose",
            10,
        )

        self.marker_pub = self.create_publisher(
            Marker,
            "/teleop/right_arm/ee_marker",
            10,
        )

        self.twist_sub = self.create_subscription(
            TwistStamped,
            "/teleop/right_arm/twist_cmd",
            self.twist_callback,
            10,
        )

        # Start position of the virtual gripper in robot base frame
        self.x = 0.45
        self.y = 0.0
        self.z = 0.35

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

        # Simple workspace limits
        self.x_min = 0.20
        self.x_max = 0.75

        self.y_min = -0.45
        self.y_max = 0.45

        self.z_min = 0.10
        self.z_max = 0.75

        self.last_time = self.get_clock().now()

        timer_period = 1.0 / self.publish_rate_hz
        self.timer = self.create_timer(timer_period, self.update)

        self.get_logger().info("Virtual end-effector simulator started.")
        self.get_logger().info("Subscribing: /teleop/right_arm/twist_cmd")
        self.get_logger().info("Publishing:  /teleop/right_arm/ee_pose")
        self.get_logger().info("Publishing:  /teleop/right_arm/ee_marker")

    def twist_callback(self, msg: TwistStamped):
        self.vx = msg.twist.linear.x
        self.vy = msg.twist.linear.y
        self.vz = msg.twist.linear.z

    @staticmethod
    def clamp(value, min_value, max_value):
        return max(min_value, min(max_value, value))

    def update(self):
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now

        # Integrate velocity into position
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt

        # Keep virtual gripper inside workspace
        self.x = self.clamp(self.x, self.x_min, self.x_max)
        self.y = self.clamp(self.y, self.y_min, self.y_max)
        self.z = self.clamp(self.z, self.z_min, self.z_max)

        self.publish_pose(now)
        self.publish_marker(now)

    def publish_pose(self, now):
        pose_msg = PoseStamped()
        pose_msg.header.stamp = now.to_msg()
        pose_msg.header.frame_id = self.frame_id

        pose_msg.pose.position.x = self.x
        pose_msg.pose.position.y = self.y
        pose_msg.pose.position.z = self.z

        # Fixed neutral orientation
        pose_msg.pose.orientation.x = 0.0
        pose_msg.pose.orientation.y = 0.0
        pose_msg.pose.orientation.z = 0.0
        pose_msg.pose.orientation.w = 1.0

        self.pose_pub.publish(pose_msg)

    def publish_marker(self, now):
        marker = Marker()
        marker.header.stamp = now.to_msg()
        marker.header.frame_id = self.frame_id

        marker.ns = "virtual_right_gripper"
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD

        marker.pose.position.x = self.x
        marker.pose.position.y = self.y
        marker.pose.position.z = self.z
        marker.pose.orientation.w = 1.0

        marker.scale.x = 0.08
        marker.scale.y = 0.08
        marker.scale.z = 0.08

        marker.color.r = 0.1
        marker.color.g = 1.0
        marker.color.b = 0.1
        marker.color.a = 1.0

        self.marker_pub.publish(marker)


def main():
    rclpy.init()
    node = VirtualEndEffectorSimulator()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
