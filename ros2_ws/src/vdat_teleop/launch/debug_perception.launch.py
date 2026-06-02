from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    webcam_teleop_node = Node(
        package="vdat_teleop",
        executable="webcam_teleop_node",
        name="webcam_teleop_node",
        output="screen",
        parameters=[
            {
                "camera_index": 0,
                "publish_rate_hz": 30.0,
                "depth_speed": 0.12,
            }
        ],
    )

    virtual_ee_simulator_node = Node(
        package="vdat_teleop",
        executable="virtual_ee_simulator_node",
        name="virtual_ee_simulator_node",
        output="screen",
        parameters=[
            {
                "frame_id": "map",
                "publish_rate_hz": 30.0,
            }
        ],
    )

    scene_objects_node = Node(
        package="vdat_teleop",
        executable="scene_objects_node",
        name="scene_objects_node",
        output="screen",
        parameters=[
            {
                "frame_id": "map",
            }
        ],
    )

    return LaunchDescription(
        [
            webcam_teleop_node,
            virtual_ee_simulator_node,
            scene_objects_node,
        ]
    )
