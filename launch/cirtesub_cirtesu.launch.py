from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    battery_status_config = PathJoinSubstitution([
        FindPackageShare("cirtesub_stonefish"),
        "config", "battery_status_simulated.yaml"
    ])

    leak_sensors_config = PathJoinSubstitution([
        FindPackageShare("cirtesub_stonefish"),
        "config", "leak_sensors_simulated.yaml"
    ])

    namespace_action = GroupAction(
        actions=[
            IncludeLaunchDescription(
                PathJoinSubstitution([
                    FindPackageShare('stonefish_ros2'), 'launch', 'stonefish_simulator.launch.py'
                ]),
                launch_arguments={
                    'simulation_data': PathJoinSubstitution([
                        FindPackageShare('cirtesub_stonefish'), 'data'
                    ]),
                    'scenario_desc': PathJoinSubstitution([
                        FindPackageShare('cirtesub_stonefish'), 'scenarios', 'cirtesub_cirtesu_arucos.scn'
                    ]),
                    'simulation_rate': '50.0',
                    'window_res_x': '800',
                    'window_res_y': '600',
                    'rendering_quality': 'low'
                }.items()
            ),
        ]
    )

    static_transform_publisher_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="world2ned",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
            "--roll",
            "0",
            "--pitch",
            "0",
            "--yaw",
            "3.1415",
            "--frame-id",
            "world",
            "--child-frame-id",
            "world_ned",
        ],
        output="screen",
    )

    dvl_to_twist_node = Node(
        package="cirtesub_stonefish",
        executable="dvl_to_twist_node",
        name="dvl_to_twist",
        output="screen",
    )

    battery_status_simulated_node = Node(
        package="cirtesub_stonefish",
        executable="battery_status_simulated",
        name="battery_status_simulated",
        output="screen",
        parameters=[battery_status_config],
    )

    leak_sensors_simulated_node = Node(
        package="cirtesub_stonefish",
        executable="leak_sensors_simulated",
        name="leak_sensors_simulated",
        output="screen",
        parameters=[leak_sensors_config],
    )

    return LaunchDescription([
        namespace_action,
        dvl_to_twist_node,
        battery_status_simulated_node,
        leak_sensors_simulated_node,
        static_transform_publisher_node,
    ])
