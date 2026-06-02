import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    EnvironmentVariable,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_param_builder import ParameterBuilder
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_rviz = LaunchConfiguration("use_rviz")
    show_scene_cameras = LaunchConfiguration("show_scene_cameras")
    repo_path = LaunchConfiguration("repo_path")

    robot_controllers = PathJoinSubstitution(
        [FindPackageShare("vdat_gazebo"), "config", "panda_gazebo_controllers.yaml"]
    )
    initial_positions = PathJoinSubstitution(
        [FindPackageShare("vdat_gazebo"), "config", "initial_positions.yaml"]
    )

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("vdat_gazebo"), "urdf", "panda_gazebo.urdf.xacro"]
            ),
            " initial_positions_file:=",
            initial_positions,
            " controllers_file:=",
            robot_controllers,
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    moveit_config = (
        MoveItConfigsBuilder("moveit_resources_panda")
        .joint_limits(file_path="config/hard_joint_limits.yaml")
        .to_moveit_configs()
    )

    servo_params = {
        "moveit_servo": ParameterBuilder("moveit_servo")
        .yaml("config/panda_simulated_config.yaml")
        .to_dict()
    }

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [FindPackageShare("vdat_gazebo"), "launch", "panda_pick_place.launch.py"]
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "enable_scene_cameras": show_scene_cameras,
        }.items(),
    )

    rviz_config_file = os.path.join(
        get_package_share_directory("moveit_servo"),
        "config",
        "demo_rviz_config_ros.rviz",
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            robot_description,
            moveit_config.robot_description_semantic,
            {"use_sim_time": use_sim_time},
        ],
        condition=IfCondition(use_rviz),
    )

    servo_node = Node(
        package="moveit_servo",
        executable="servo_node",
        name="servo_node",
        output="screen",
        parameters=[
            servo_params,
            {"update_period": 0.01, "planning_group_name": "panda_arm"},
            robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
            {"use_sim_time": use_sim_time},
        ],
    )

    switch_servo_to_twist = ExecuteProcess(
        cmd=[
            "ros2",
            "service",
            "call",
            "/servo_node/switch_command_type",
            "moveit_msgs/srv/ServoCommandType",
            "{command_type: 1}",
        ],
        output="screen",
    )

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

    gripper_relay_node = Node(
        package="vdat_teleop",
        executable="gripper_relay_node",
        name="gripper_relay_node",
        output="screen",
        parameters=[
            {
                "command_type": "action",
                "output_action_topic": "/panda_hand_controller/gripper_cmd",
                "open_position": 0.04,
                "closed_position": 0.0,
                "max_effort": 20.0,
            }
        ],
    )

    scene_camera_viewer_node = Node(
        package="vdat_teleop",
        executable="scene_camera_viewer_node",
        name="scene_camera_viewer_node",
        output="screen",
        parameters=[
            {
                "camera_topics": [
                    "/scene_camera_overview",
                    "/scene_camera_side",
                    "/scene_camera_gripper",
                ],
                "labels": ["Overview", "Side", "Gripper"],
                "display_scale": 0.55,
            }
        ],
        condition=IfCondition(show_scene_cameras),
    )

    default_repo = os.environ.get(
        "VDAT_REPO", "/home/shubham.ghogare/vision_dual_arm_teleop"
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("use_rviz", default_value="true"),
            DeclareLaunchArgument("show_scene_cameras", default_value="true"),
            DeclareLaunchArgument("repo_path", default_value=default_repo),
            SetEnvironmentVariable(
                name="PYTHONPATH",
                value=[
                    repo_path,
                    ":",
                    EnvironmentVariable("PYTHONPATH", default_value=""),
                ],
            ),
            gazebo_launch,
            rviz_node,
            TimerAction(period=12.0, actions=[servo_node]),
            TimerAction(period=14.0, actions=[switch_servo_to_twist]),
            TimerAction(period=15.0, actions=[webcam_teleop_node]),
            TimerAction(period=16.0, actions=[servo_twist_relay_node]),
            TimerAction(period=17.0, actions=[gripper_relay_node]),
            TimerAction(period=8.0, actions=[scene_camera_viewer_node]),
        ]
    )
