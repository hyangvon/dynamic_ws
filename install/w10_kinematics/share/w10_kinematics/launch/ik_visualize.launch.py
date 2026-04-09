import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get package directories
    w10_sim_dir = get_package_share_directory('w10_sim')
    urdf_file = os.path.join(w10_sim_dir, 'urdf', 'w10.urdf')
    
    # Read URDF file content
    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    # Node: robot_state_publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}],
        output='screen'
    )

    # Node: ik_visualizer
    ik_visualizer_node = Node(
        package='w10_kinematics',
        executable='ik_visualize',
        output='screen'
    )

    # Node: RViz
    rviz_config_dir = os.path.join(w10_sim_dir, 'rviz', 'w10.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_dir],
        output='screen'
    )

    # Create launch description
    ld = LaunchDescription([
        robot_state_publisher_node,
        ik_visualizer_node,
        rviz_node,
    ])

    return ld
