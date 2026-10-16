"""Tanque CIRTESU con CIRTESUB, los brazos Alpha y la red deformable."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    share = FindPackageShare('cirtesub_stonefish')

    simulator = Node(
        package='stonefish_net',
        executable='stonefish_net_simulator',
        namespace='stonefish_ros2',
        name='stonefish_simulator',
        output='screen',
        arguments=[
            LaunchConfiguration('simulation_data'),
            LaunchConfiguration('scenario'),
            LaunchConfiguration('simulation_rate'),
            LaunchConfiguration('window_width'),
            LaunchConfiguration('window_height'),
            LaunchConfiguration('rendering_quality'),
            LaunchConfiguration('net_config'),
            LaunchConfiguration('damage_seed'),
        ],
    )

    dvl_to_twist_node = Node(
        package='cirtesub_stonefish',
        executable='dvl_to_twist_node',
        name='dvl_to_twist',
        output='screen',
    )

    battery_status_simulated_node = Node(
        package='cirtesub_stonefish',
        executable='battery_status_simulated',
        name='battery_status_simulated',
        output='screen',
        parameters=[PathJoinSubstitution([
            share, 'config', 'battery_status_simulated.yaml',
        ])],
    )

    leak_sensors_simulated_node = Node(
        package='cirtesub_stonefish',
        executable='leak_sensors_simulated',
        name='leak_sensors_simulated',
        output='screen',
        parameters=[PathJoinSubstitution([
            share, 'config', 'leak_sensors_simulated.yaml',
        ])],
    )

    static_transform_publisher_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='world2ned',
        arguments=[
            '--x', '0',
            '--y', '0',
            '--z', '0',
            '--roll', '0',
            '--pitch', '0',
            '--yaw', '3.1415',
            '--frame-id', 'world',
            '--child-frame-id', 'world_ned',
        ],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'scenario',
            default_value=PathJoinSubstitution([
                share, 'scenarios', 'cirtesub_cirtesu_net.scn',
            ]),
            description='Escenario del tanque con CIRTESUB, los Alpha y los looks de la red.',
        ),
        DeclareLaunchArgument(
            'simulation_data',
            default_value=PathJoinSubstitution([share, 'data']),
            description='Carpeta de mallas y texturas del escenario.',
        ),
        DeclareLaunchArgument(
            'net_config',
            default_value=PathJoinSubstitution([share, 'config', 'cirtesub_net.yaml']),
            description='Configuración de la red deformable.',
        ),
        DeclareLaunchArgument('simulation_rate', default_value='200.0'),
        DeclareLaunchArgument('window_width', default_value='800'),
        DeclareLaunchArgument('window_height', default_value='600'),
        DeclareLaunchArgument(
            'rendering_quality', default_value='noshadows',
            description='Calidad gráfica: low, medium, high o noshadows.',
            choices=['low', 'medium', 'high', 'noshadows'],
        ),
        DeclareLaunchArgument(
            'damage_seed', default_value='-1',
            description='Semilla de los agujeros; -1 usa la del YAML.',
        ),
        simulator,
        dvl_to_twist_node,
        battery_status_simulated_node,
        leak_sensors_simulated_node,
        static_transform_publisher_node,
    ])
