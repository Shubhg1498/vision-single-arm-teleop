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

        self.publish_count = 0
        self.timer = self.create_timer(0.5, self.publish_objects)

        self.get_logger().info("Scene objects node started.")
        self.get_logger().info("Publishing collision objects to /collision_object")
        self.get_logger().info("Publishing RViz markers to /teleop/scene_markers")

    def create_collision_box(self, object_id, size_x, size_y, size_z, x, y, z):
        obj = CollisionObject()
        obj.header.frame_id = self.frame_id
        obj.id = object_id

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [size_x, size_y, size_z]

        pose = Pose()
        pose.position.x = x
        pose.position.y = y
        pose.position.z = z
        pose.orientation.w = 1.0

        obj.primitives.append(primitive)
        obj.primitive_poses.append(pose)
        obj.operation = CollisionObject.ADD

        return obj

    def create_marker(self, marker_id, name, size_x, size_y, size_z, x, y, z, r, g, b, a=1.0):
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "teleop_scene"
        marker.id = marker_id
        marker.type = Marker.CUBE
        marker.action = Marker.ADD

        marker.pose.position.x = x
        marker.pose.position.y = y
        marker.pose.position.z = z
        marker.pose.orientation.w = 1.0

        marker.scale.x = size_x
        marker.scale.y = size_y
        marker.scale.z = size_z

        marker.color.r = r
        marker.color.g = g
        marker.color.b = b
        marker.color.a = a

        marker.text = name

        return marker

    def publish_objects(self):
        objects = [
            self.create_collision_box(
                object_id="table",
                size_x=0.9,
                size_y=0.8,
                size_z=0.04,
                x=0.45,
                y=0.0,
                z=0.18,
            ),
            self.create_collision_box(
                object_id="pick_cube",
                size_x=0.05,
                size_y=0.05,
                size_z=0.05,
                x=0.45,
                y=0.15,
                z=0.225,
            ),
            self.create_collision_box(
                object_id="place_zone",
                size_x=0.12,
                size_y=0.12,
                size_z=0.01,
                x=0.45,
                y=-0.18,
                z=0.225,
            ),
        ]

        for obj in objects:
            self.collision_pub.publish(obj)

        markers = MarkerArray()
        markers.markers.append(
            self.create_marker(
                marker_id=0,
                name="table",
                size_x=0.9,
                size_y=0.8,
                size_z=0.04,
                x=0.45,
                y=0.0,
                z=0.18,
                r=0.45,
                g=0.30,
                b=0.15,
                a=0.8,
            )
        )
        markers.markers.append(
            self.create_marker(
                marker_id=1,
                name="pick_cube",
                size_x=0.05,
                size_y=0.05,
                size_z=0.05,
                x=0.45,
                y=0.15,
                z=0.225,
                r=0.0,
                g=0.4,
                b=1.0,
                a=1.0,
            )
        )
        markers.markers.append(
            self.create_marker(
                marker_id=2,
                name="place_zone",
                size_x=0.12,
                size_y=0.12,
                size_z=0.01,
                x=0.45,
                y=-0.18,
                z=0.225,
                r=0.0,
                g=1.0,
                b=0.0,
                a=0.8,
            )
        )

        self.marker_pub.publish(markers)

        self.publish_count += 1

        if self.publish_count <= 5:
            self.get_logger().info("Published table, pick_cube, and place_zone.")

        # Keep publishing markers, but collision objects only need repeated startup publishing.
        # This timer can continue running safely.


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