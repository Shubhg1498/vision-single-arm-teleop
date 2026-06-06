from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    camera_index = LaunchConfiguration("camera_index")
    camera_device = LaunchConfiguration("camera_device")
    flip_horizontal = LaunchConfiguration("flip_horizontal")
    moveit_servo_demo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare("moveit_servo"),
            "/launch/demo_ros_api.launch.py",
        ])
    )

    scene_objects_node = Node(
        package="vdat_teleop",
        executable="scene_objects_node",
        name="scene_objects_node",
        output="screen",
    )

    manipulation_object_node = Node(
        package="vdat_teleop",
        executable="demo_manipulation_object_node",
        name="demo_manipulation_object_node",
        output="screen",
        parameters=[
            {
                "grasp_distance_threshold": 0.18,
                "world_frame": "panda_link0",
                "gripper_frame": "panda_hand",
            }
        ],
    )

    webcam_teleop_node = Node(
        package="vdat_teleop",
        executable="webcam_teleop_node",
        name="webcam_teleop_node",
        output="screen",
        parameters=[
            {
                "camera_index": camera_index,
                "camera_device": camera_device,
                "flip_horizontal": flip_horizontal,
                "publish_rate_hz": 30.0,
                "depth_speed": 0.12,
            }
        ],
    )

    servo_twist_relay_node = Node(
        package="vdat_teleop",
        executable="servo_twist_relay_node",
        name="servo_twist_relay_node",
        output="screen",
        parameters=[
            {
                "scale": 0.30,
                "max_linear_speed": 0.06,
                "max_linear_accel": 0.18,
                "smoothing_alpha": 0.20,
                "servo_frame_id": "panda_link0",
                "input_topic": "/teleop/right_arm/twist_cmd",
                "output_topic": "/servo_node/delta_twist_cmds",
            }
        ],
    )

    # Optional. Keep disabled if your Panda gripper controller is unavailable.
    # gripper_relay_node = Node(
    #     package="vdat_teleop",
    #     executable="gripper_relay_node",
    #     name="gripper_relay_node",
    #     output="screen",
    # )

    return LaunchDescription(
        [
            DeclareLaunchArgument("camera_index", default_value="0"),
            DeclareLaunchArgument(
                "camera_device",
                default_value="",
                description="Optional /dev/video path (overrides camera_index when set)",
            ),
            DeclareLaunchArgument(
                "flip_horizontal",
                default_value="true",
                description="Mirror image horizontally (mirror-style teleop)",
            ),
            moveit_servo_demo,

            # Wait a little for MoveIt/RViz/Servo to initialize.
            TimerAction(period=4.0, actions=[scene_objects_node]),
            TimerAction(period=5.0, actions=[manipulation_object_node]),
            TimerAction(period=6.0, actions=[webcam_teleop_node]),
            TimerAction(period=7.0, actions=[servo_twist_relay_node]),

            # Enable this only if gripper controller works.
            # TimerAction(period=8.0, actions=[gripper_relay_node]),
        ]
    )
