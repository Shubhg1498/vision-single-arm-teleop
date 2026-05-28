import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Pose
from moveit_msgs.msg import CollisionObject, PlanningScene
from shape_msgs.msg import SolidPrimitive
from visualization_msgs.msg import Marker, MarkerArray


class SceneObjectsNode(Node):
    def __init__(self):
        super().__init__("scene_objects_node")

        self.declare_parameter("frame_id", "panda_link0")
        self.declare_parameter("publish_rate_hz", 1.0)
        self.declare_parameter("publish_collision_objects", True)

        self.frame_id = self.get_parameter("frame_id").value
        self.publish_collision_objects = bool(
            self.get_parameter("publish_collision_objects").value
        )

        self.planning_scene_pub = self.create_publisher(
            PlanningScene,
            "/planning_scene",
            10,
        )

        self.collision_object_pub = self.create_publisher(
            CollisionObject,
            "/collision_object",
            10,
        )

        self.marker_pub = self.create_publisher(
            MarkerArray,
            "/teleop/scene_markers",
            10,
        )

        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self.timer = self.create_timer(1.0 / publish_rate_hz, self.publish_scene)

        self.publish_count = 0

        self.get_logger().info("Scene objects node started.")
        self.get_logger().info(f"Frame ID: {self.frame_id}")
        self.get_logger().info(
            f"Collision objects enabled: {self.publish_collision_objects}"
        )
        self.get_logger().info("Publishing:")
        self.get_logger().info("  /planning_scene")
        self.get_logger().info("  /collision_object")
        self.get_logger().info("  /teleop/scene_markers")

    def make_pose(self, x, y, z):
        pose = Pose()
        pose.position.x = float(x)
        pose.position.y = float(y)
        pose.position.z = float(z)
        pose.orientation.w = 1.0
        return pose

    def create_collision_box(
        self,
        object_id,
        size_x,
        size_y,
        size_z,
        x,
        y,
        z,
    ):
        obj = CollisionObject()
        obj.header.frame_id = self.frame_id
        obj.id = object_id

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [
            float(size_x),
            float(size_y),
            float(size_z),
        ]

        obj.primitives.append(primitive)
        obj.primitive_poses.append(self.make_pose(x, y, z))
        obj.operation = CollisionObject.ADD

        return obj

    def create_marker(
        self,
        marker_id,
        name,
        size_x,
        size_y,
        size_z,
        x,
        y,
        z,
        r,
        g,
        b,
        a=1.0,
    ):
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

    def get_scene_objects(self):
        """
        Safe object layout for Panda Servo demo.

        Important:
        - Panda base frame is panda_link0.
        - Table is placed low enough to avoid initial collision.
        - Cube is on top of visual table.
        - Place zone is visual-only.
        """

        table = {
            "id": "table",
            "size": (0.80, 0.60, 0.04),
            "pose": (0.55, 0.00, -0.04),
            "color": (0.45, 0.30, 0.15, 0.75),
            "collision": True,
        }

        pick_cube = {
            "id": "pick_cube",
            "size": (0.05, 0.05, 0.05),
            "pose": (0.50, 0.22, 0.04),
            "color": (0.0, 0.4, 1.0, 1.0),
            "collision": True,
        }

        place_zone = {
            "id": "place_zone",
            "size": (0.12, 0.12, 0.01),
            "pose": (0.50, -0.22, 0.015),
            "color": (0.0, 1.0, 0.0, 0.8),
            "collision": False,
        }

        return [table, pick_cube, place_zone]

    def publish_collision_scene(self, objects):
        collision_objects = []

        for obj_data in objects:
            if not obj_data["collision"]:
                continue

            sx, sy, sz = obj_data["size"]
            x, y, z = obj_data["pose"]

            collision_obj = self.create_collision_box(
                object_id=obj_data["id"],
                size_x=sx,
                size_y=sy,
                size_z=sz,
                x=x,
                y=y,
                z=z,
            )

            collision_objects.append(collision_obj)

            # Also publish individual collision objects.
            # This helps MoveIt/RViz consume them reliably.
            self.collision_object_pub.publish(collision_obj)

        scene = PlanningScene()
        scene.is_diff = True
        scene.world.collision_objects = collision_objects

        self.planning_scene_pub.publish(scene)

    def publish_visual_markers(self, objects):
        markers = MarkerArray()

        for idx, obj_data in enumerate(objects):
            sx, sy, sz = obj_data["size"]
            x, y, z = obj_data["pose"]
            r, g, b, a = obj_data["color"]

            markers.markers.append(
                self.create_marker(
                    marker_id=idx,
                    name=obj_data["id"],
                    size_x=sx,
                    size_y=sy,
                    size_z=sz,
                    x=x,
                    y=y,
                    z=z,
                    r=r,
                    g=g,
                    b=b,
                    a=a,
                )
            )

        self.marker_pub.publish(markers)

    def publish_scene(self):
        objects = self.get_scene_objects()

        self.publish_visual_markers(objects)

        if self.publish_collision_objects:
            self.publish_collision_scene(objects)

        self.publish_count += 1

        if self.publish_count <= 5:
            self.get_logger().info(
                "Published collision-aware scene: table, pick_cube, place_zone marker."
            )


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