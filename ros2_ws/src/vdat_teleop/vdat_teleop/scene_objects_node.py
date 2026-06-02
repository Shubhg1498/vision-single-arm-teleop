import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Pose
from moveit_msgs.msg import CollisionObject
from shape_msgs.msg import SolidPrimitive
from visualization_msgs.msg import Marker, MarkerArray


class SceneObjectsNode(Node):
    def __init__(self):
        super().__init__("scene_objects_node")

        self.declare_parameter("frame_id", "panda_link0")
        self.frame_id = self.get_parameter("frame_id").value

        self.collision_pub = self.create_publisher(
            CollisionObject,
            "/collision_object",
            10,
        )

        self.marker_pub = self.create_publisher(
            MarkerArray,
            "/teleop/scene_markers",
            10,
        )

        self.timer = self.create_timer(0.5, self.publish_scene)

        self.get_logger().info("Scene objects node started.")
        self.get_logger().info("Publishing table collision + place zone marker.")
        self.get_logger().info("Pick object is handled by demo_manipulation_object_node.")

    def make_pose(self, x, y, z):
        pose = Pose()
        pose.position.x = float(x)
        pose.position.y = float(y)
        pose.position.z = float(z)
        pose.orientation.w = 1.0
        return pose

    def create_collision_box(self, object_id, size_x, size_y, size_z, x, y, z):
        obj = CollisionObject()
        obj.header.frame_id = self.frame_id
        obj.id = object_id

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [float(size_x), float(size_y), float(size_z)]

        obj.primitives.append(primitive)
        obj.primitive_poses.append(self.make_pose(x, y, z))
        obj.operation = CollisionObject.ADD

        return obj

    def create_marker(self, marker_id, name, size_x, size_y, size_z, x, y, z, r, g, b, a):
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = "teleop_scene"
        marker.id = marker_id
        marker.type = Marker.CUBE
        marker.action = Marker.ADD

        marker.pose = self.make_pose(x, y, z)

        marker.scale.x = float(size_x)
        marker.scale.y = float(size_y)
        marker.scale.z = float(size_z)

        marker.color.r = float(r)
        marker.color.g = float(g)
        marker.color.b = float(b)
        marker.color.a = float(a)

        marker.text = name
        return marker

    def publish_scene(self):
        # Safe collision table. Keep it low enough to avoid Panda startup collision.
        table = self.create_collision_box(
            object_id="demo_table",
            size_x=0.80,
            size_y=0.60,
            size_z=0.04,
            x=0.55,
            y=0.00,
            z=-0.04,
        )
        self.collision_pub.publish(table)

        markers = MarkerArray()

        # Visual table overlay
        markers.markers.append(
            self.create_marker(
                marker_id=0,
                name="table",
                size_x=0.80,
                size_y=0.60,
                size_z=0.04,
                x=0.55,
                y=0.00,
                z=-0.04,
                r=0.45,
                g=0.30,
                b=0.15,
                a=0.75,
            )
        )

        # Place zone should be visual only, not collision.
        markers.markers.append(
            self.create_marker(
                marker_id=1,
                name="place_zone",
                size_x=0.14,
                size_y=0.14,
                size_z=0.012,
                x=0.55,
                y=-0.24,
                z=0.005,
                r=0.0,
                g=1.0,
                b=0.0,
                a=0.85,
            )
        )

        self.marker_pub.publish(markers)


def main():
    rclpy.init()
    node = SceneObjectsNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()