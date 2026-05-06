from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    rviz_config_file = PathJoinSubstitution([
        FindPackageShare("cirtesub_stonefish"),
        "config", "cirtesub.rviz"
    ])

    battery_status_config = PathJoinSubstitution([
        FindPackageShare("cirtesub_stonefish"),
        "config", "battery_status_simulated.yaml"
    ])

    leak_sensors_config = PathJoinSubstitution([
        FindPackageShare("cirtesub_stonefish"),
        "config", "leak_sensors_simulated.yaml"
    ])

    description_file_fish = PathJoinSubstitution([
        FindPackageShare("cirtesub_description"),
        "urdf", "cirtesub_dual_alpha.urdf.xacro"
    ])

    lookup_csv_file = PathJoinSubstitution([
        FindPackageShare("thrusters_hardware_interface"),
        "config", "t500_lookup.csv"
    ])

    robot_description_cirtesub = Command([
        "xacro", " ",
        description_file_fish, " ",
        "lookup_csv:=", lookup_csv_file, " ",
        "use_sim:=true"
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

    dvl_to_twist_node = Node(
        package="cirtesub_stonefish",
        executable="dvl_to_twist.py",
        name="dvl_to_twist",
        output="screen",
    )

    rsp_node_cirtesub = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher_cirtesub",
        output="screen",
        parameters=[{
            "robot_description": robot_description_cirtesub
        }],
        remappings=[
            ("/robot_description", "/cirtesub/robot_description"),
            ("/joint_states", "/cirtesub/joint_states")
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
    )

    battery_status_simulated_node = Node(
        package="cirtesub_stonefish",
        executable="battery_status_simulated.py",
        name="battery_status_simulated",
        output="screen",
        parameters=[battery_status_config],
    )

    leak_sensors_simulated_node = Node(
        package="cirtesub_stonefish",
        executable="leak_sensors_simulated.py",
        name="leak_sensors_simulated",
        output="screen",
        parameters=[leak_sensors_config],
    )

    return LaunchDescription([
        namespace_action,
        rsp_node_cirtesub,
        rviz_node,
        odom_tf_node,
        dvl_to_twist_node,
        battery_status_simulated_node,
        leak_sensors_simulated_node,
        static_transform_publisher_node,
    ])
