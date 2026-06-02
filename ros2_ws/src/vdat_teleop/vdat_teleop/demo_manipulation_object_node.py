import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Pose
from std_msgs.msg import Bool

from moveit_msgs.msg import (
    AttachedCollisionObject,
    CollisionObject,
    ObjectColor,
    PlanningScene,
)

from shape_msgs.msg import SolidPrimitive
from visualization_msgs.msg import Marker, MarkerArray

import tf2_ros


class DemoManipulationObjectNode(Node):
    def __init__(self):
        super().__init__("demo_manipulation_object_node")

        self.declare_parameter("world_frame", "panda_link0")
        self.declare_parameter("gripper_frame", "panda_hand")
        self.declare_parameter("object_id", "demo_pick_object")
        self.declare_parameter("grasp_distance_threshold", 0.16)
        self.declare_parameter("publish_rate_hz", 20.0)

        self.world_frame = self.get_parameter("world_frame").value
        self.gripper_frame = self.get_parameter("gripper_frame").value
        self.object_id = self.get_parameter("object_id").value
        self.grasp_distance_threshold = float(
            self.get_parameter("grasp_distance_threshold").value
        )

        self.marker_pub = self.create_publisher(
            MarkerArray,
            "/teleop/manipulation_object_markers",
            10,
        )

        self.collision_pub = self.create_publisher(
            CollisionObject,
            "/collision_object",
            10,
        )

        self.attached_collision_pub = self.create_publisher(
            AttachedCollisionObject,
            "/attached_collision_object",
            10,
        )

        self.planning_scene_pub = self.create_publisher(
            PlanningScene,
            "/planning_scene",
            10,
        )

        self.gripper_sub = self.create_subscription(
            Bool,
            "/teleop/right_gripper/close",
            self.gripper_callback,
            10,
        )

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Object dimensions: a small block with visual decorations.
        self.size_x = 0.065
        self.size_y = 0.065
        self.size_z = 0.085

        # Initial object pose in panda_link0.
        # Table top is around z = -0.02 to 0.00, so object center is above it.
        self.object_x = 0.55
        self.object_y = 0.22
        self.object_z = 0.055

        # When attached, place object slightly below panda_hand.
        self.attach_offset_x = 0.00
        self.attach_offset_y = 0.00
        self.attach_offset_z = -0.085

        self.object_attached = False
        self.gripper_closed = False
        self.prev_gripper_closed = False

        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self.timer = self.create_timer(1.0 / publish_rate_hz, self.update)

        self.get_logger().info("Demo manipulation object node started.")
        self.get_logger().info("Proper behavior:")
        self.get_logger().info("  Object exists as world CollisionObject.")
        self.get_logger().info("  Pinch near object -> AttachedCollisionObject on panda_hand.")
        self.get_logger().info("  Release -> detach and re-add to world.")
        self.get_logger().info(f"World frame:   {self.world_frame}")
        self.get_logger().info(f"Gripper frame: {self.gripper_frame}")

    def gripper_callback(self, msg: Bool):
        self.gripper_closed = bool(msg.data)

    def make_pose(self, x, y, z):
        pose = Pose()
        pose.position.x = float(x)
        pose.position.y = float(y)
        pose.position.z = float(z)
        pose.orientation.w = 1.0
        return pose

    def get_gripper_position(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                self.world_frame,
                self.gripper_frame,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.05),
            )
            t = transform.transform.translation
            return t.x, t.y, t.z

        except Exception as exc:
            self.get_logger().warn(
                f"TF unavailable {self.world_frame} -> {self.gripper_frame}: {exc}",
                throttle_duration_sec=2.0,
            )
            return None

    @staticmethod
    def distance(a, b):
        return math.sqrt(
            (a[0] - b[0]) ** 2
            + (a[1] - b[1]) ** 2
            + (a[2] - b[2]) ** 2
        )

    def create_object_primitive(self):
        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [
            self.size_x,
            self.size_y,
            self.size_z,
        ]
        return primitive

    def create_world_collision_object(self, operation=CollisionObject.ADD):
        obj = CollisionObject()
        obj.header.frame_id = self.world_frame
        obj.id = self.object_id

        if operation == CollisionObject.ADD:
            obj.primitives.append(self.create_object_primitive())
            obj.primitive_poses.append(
                self.make_pose(self.object_x, self.object_y, self.object_z)
            )

        obj.operation = operation
        return obj

    def publish_world_object_add(self):
        obj = self.create_world_collision_object(CollisionObject.ADD)
        self.collision_pub.publish(obj)

        scene = PlanningScene()
        scene.is_diff = True
        scene.world.collision_objects.append(obj)

        color = ObjectColor()
        color.id = self.object_id
        color.color.r = 0.05
        color.color.g = 0.25
        color.color.b = 1.0
        color.color.a = 1.0
        scene.object_colors.append(color)

        self.planning_scene_pub.publish(scene)

    def publish_world_object_remove(self):
        obj = self.create_world_collision_object(CollisionObject.REMOVE)
        self.collision_pub.publish(obj)

        scene = PlanningScene()
        scene.is_diff = True
        scene.world.collision_objects.append(obj)
        self.planning_scene_pub.publish(scene)

    def publish_attach_object(self):
        # Remove from world first.
        self.publish_world_object_remove()

        attached = AttachedCollisionObject()
        attached.link_name = self.gripper_frame
        attached.touch_links = [
            "panda_hand",
            "panda_leftfinger",
            "panda_rightfinger",
        ]

        obj = CollisionObject()
        obj.header.frame_id = self.gripper_frame
        obj.id = self.object_id
        obj.primitives.append(self.create_object_primitive())

        # Pose is relative to panda_hand while attached.
        obj.primitive_poses.append(
            self.make_pose(
                self.attach_offset_x,
                self.attach_offset_y,
                self.attach_offset_z,
            )
        )
        obj.operation = CollisionObject.ADD

        attached.object = obj

        self.attached_collision_pub.publish(attached)

        scene = PlanningScene()
        scene.is_diff = True
        scene.robot_state.attached_collision_objects.append(attached)
        scene.robot_state.is_diff = True

        color = ObjectColor()
        color.id = self.object_id
        color.color.r = 0.05
        color.color.g = 0.25
        color.color.b = 1.0
        color.color.a = 1.0
        scene.object_colors.append(color)

        self.planning_scene_pub.publish(scene)

    def publish_detach_object(self):
        # Remove attached object.
        attached = AttachedCollisionObject()
        attached.link_name = self.gripper_frame

        obj = CollisionObject()
        obj.header.frame_id = self.gripper_frame
        obj.id = self.object_id
        obj.operation = CollisionObject.REMOVE

        attached.object = obj

        self.attached_collision_pub.publish(attached)

        scene = PlanningScene()
        scene.is_diff = True
        scene.robot_state.attached_collision_objects.append(attached)
        scene.robot_state.is_diff = True
        self.planning_scene_pub.publish(scene)

        # Re-add object to world at release pose.
        self.publish_world_object_add()

    def current_visual_pose(self):
        if self.object_attached:
            gripper_pos = self.get_gripper_position()
            if gripper_pos is not None:
                return (
                    gripper_pos[0] + self.attach_offset_x,
                    gripper_pos[1] + self.attach_offset_y,
                    gripper_pos[2] + self.attach_offset_z,
                )

        return self.object_x, self.object_y, self.object_z

    def create_box_marker(self, marker_id, x, y, z):
        marker = Marker()
        marker.header.frame_id = self.world_frame
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "manipulation_object"
        marker.id = marker_id
        marker.type = Marker.CUBE
        marker.action = Marker.ADD

        marker.pose = self.make_pose(x, y, z)
        marker.scale.x = self.size_x
        marker.scale.y = self.size_y
        marker.scale.z = self.size_z

        # Nice blue body
        marker.color.r = 0.05
        marker.color.g = 0.25
        marker.color.b = 1.0
        marker.color.a = 1.0

        return marker

    def create_band_marker(self, marker_id, x, y, z, orientation):
        marker = Marker()
        marker.header.frame_id = self.world_frame
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "manipulation_object"
        marker.id = marker_id
        marker.type = Marker.CUBE
        marker.action = Marker.ADD

        marker.pose = self.make_pose(x, y, z)

        if orientation == "x":
            marker.scale.x = self.size_x + 0.008
            marker.scale.y = 0.012
            marker.scale.z = self.size_z + 0.008
        else:
            marker.scale.x = 0.012
            marker.scale.y = self.size_y + 0.008
            marker.scale.z = self.size_z + 0.008

        # Gold bands
        marker.color.r = 1.0
        marker.color.g = 0.78
        marker.color.b = 0.05
        marker.color.a = 1.0

        return marker

    def create_top_marker(self, marker_id, x, y, z):
        marker = Marker()
        marker.header.frame_id = self.world_frame
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "manipulation_object"
        marker.id = marker_id
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD

        marker.pose = self.make_pose(x, y, z + self.size_z / 2.0 + 0.018)
        marker.scale.x = 0.035
        marker.scale.y = 0.035
        marker.scale.z = 0.025

        # Red top button
        marker.color.r = 1.0
        marker.color.g = 0.1
        marker.color.b = 0.05
        marker.color.a = 1.0

        return marker

    def create_text_marker(self, marker_id, x, y, z):
        marker = Marker()
        marker.header.frame_id = self.world_frame
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "manipulation_object"
        marker.id = marker_id
        marker.type = Marker.TEXT_VIEW_FACING
        marker.action = Marker.ADD

        marker.pose = self.make_pose(x, y, z + 0.14)
        marker.scale.z = 0.035

        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 1.0

        marker.text = "ATTACHED" if self.object_attached else "PICK OBJECT"

        return marker

    def publish_visual_markers(self):
        x, y, z = self.current_visual_pose()

        markers = MarkerArray()
        markers.markers.append(self.create_box_marker(0, x, y, z))
        markers.markers.append(self.create_band_marker(1, x, y, z, "x"))
        markers.markers.append(self.create_band_marker(2, x, y, z, "y"))
        markers.markers.append(self.create_top_marker(3, x, y, z))
        markers.markers.append(self.create_text_marker(4, x, y, z))

        self.marker_pub.publish(markers)

    def update(self):
        gripper_position = self.get_gripper_position()

        if gripper_position is not None:
            object_position = self.current_visual_pose()
            dist = self.distance(gripper_position, object_position)

            # Rising edge: open -> closed, near object => attach.
            if (
                self.gripper_closed
                and not self.prev_gripper_closed
                and not self.object_attached
                and dist <= self.grasp_distance_threshold
            ):
                self.object_attached = True
                self.publish_attach_object()
                self.get_logger().info(
                    f"Object ATTACHED to {self.gripper_frame}. Distance: {dist:.3f} m"
                )

            # Falling edge: closed -> open, attached => detach.
            if (
                not self.gripper_closed
                and self.prev_gripper_closed
                and self.object_attached
            ):
                release_pose = self.current_visual_pose()
                self.object_x = release_pose[0]
                self.object_y = release_pose[1]
                self.object_z = release_pose[2]

                self.object_attached = False
                self.publish_detach_object()
                self.get_logger().info(
                    f"Object DETACHED at x={self.object_x:.3f}, "
                    f"y={self.object_y:.3f}, z={self.object_z:.3f}"
                )

        # While not attached, keep world object alive.
        if not self.object_attached:
            self.publish_world_object_add()

        self.publish_visual_markers()
        self.prev_gripper_closed = self.gripper_closed


def main():
    rclpy.init()
    node = DemoManipulationObjectNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
