import os
from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution, EnvironmentVariable, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    rviz_config_file = PathJoinSubstitution([
        EnvironmentVariable("HOME"),
        "entornos_stonefish", "src", "cirtesub_stonefish", "config", "cirtesub.rviz"
    ])

    urdf_file_fish = PathJoinSubstitution([
        EnvironmentVariable("HOME"),
        "entornos_stonefish", "src",
        "cirtesub_stonefish", "urdf", "cirtesub_description", "cirtesub.urdf"
    ])

    description_file_cirtesu = PathJoinSubstitution([
        FindPackageShare("cirtesub_stonefish"),
        "urdf", "cirtesu", "cirtesu.urdf.xacro"
    ])

    robot_description_cirtesu = Command([
        "xacro", " ",
        description_file_cirtesu
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
                    'window_res_x': '1200',
                    'window_res_y': '800',
                    'rendering_quality': 'high'
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

    odom_tf_node = Node(
        package="cirtesub_stonefish",
        executable="odom2tf.py",
        name="odom_tf",
        remappings=[
            ("/odom_topic", "/cirtesub/odometry"),
        ],
        parameters=[{"fixed_frame": "world_ned", "base_link": "cirtesub/base_link"}],
        output="screen",
    )

    cirtesu_static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        output='screen',
        arguments=[
            "--x", "0",
            "--y", "0",
            "--z", "0.0",
            "--roll", "0.0",
            "--pitch", "3.1416",
            "--yaw", "0",
            "--frame-id", "world_ned",
            "--child-frame-id", "cirtesu_tank"
        ]
    )



    return LaunchDescription([
        namespace_action,
        odom_tf_node,
        static_transform_publisher_node,
        cirtesu_static_tf
    ])
