from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    gz_args = LaunchConfiguration("gz_args")
    enable_scene_cameras = LaunchConfiguration("enable_scene_cameras")

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

    world_path = PathJoinSubstitution(
        [FindPackageShare("vdat_gazebo"), "worlds", "pick_place.sdf"]
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "panda",
            "-allow_renaming",
            "true",
        ],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager-timeout", "120"],
    )

    panda_arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "panda_arm_controller",
            "--param-file",
            robot_controllers,
            "--controller-manager-timeout",
            "120",
        ],
    )

    panda_hand_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "panda_hand_controller",
            "--param-file",
            robot_controllers,
            "--controller-manager-timeout",
            "120",
        ],
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    scene_camera_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=[
            "scene_camera_overview",
            "scene_camera_side",
            "scene_camera_gripper",
            "scene_camera_table_top",
        ],
        output="screen",
        condition=IfCondition(enable_scene_cameras),
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])]
        ),
        launch_arguments=[("gz_args", [gz_args, " -r -v 1 ", world_path])],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("gz_args", default_value=""),
            DeclareLaunchArgument("enable_scene_cameras", default_value="true"),
            gz_sim,
            bridge,
            scene_camera_bridge,
            robot_state_publisher,
            gz_spawn_entity,
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=gz_spawn_entity,
                    on_exit=[joint_state_broadcaster_spawner],
                )
            ),
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=joint_state_broadcaster_spawner,
                    on_exit=[panda_arm_controller_spawner],
                )
            ),
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=panda_arm_controller_spawner,
                    on_exit=[panda_hand_controller_spawner],
                )
            ),
        ]
    )
