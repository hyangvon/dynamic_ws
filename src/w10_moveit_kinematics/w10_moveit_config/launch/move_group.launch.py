"""
Launch file for W10 MoveIt2 system
Starts planning scene, move group, and RViz visualization
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import yaml


def generate_launch_description():
    """Generate launch description for W10 MoveIt2 system"""
    
    # Get package directories
    w10_sim_package_dir = get_package_share_directory('w10_sim')
    w10_moveit_package_dir = get_package_share_directory('w10_moveit_kinematics')
    
    # URDF file
    urdf_file = os.path.join(w10_sim_package_dir, 'urdf', 'w10.urdf')
    
    # SRDF file
    srdf_file = os.path.join(
        w10_moveit_package_dir,
        'config', 'w10_sim.srdf'
    )
    
    # Configuration files
    kinematics_yaml = os.path.join(
        w10_moveit_package_dir,
        'config', 'kinematics.yaml'
    )
    
    joint_limits_yaml = os.path.join(
        w10_moveit_package_dir,
        'config', 'joint_limits.yaml'
    )
    
    moveit_planning_adapters_yaml = os.path.join(
        w10_moveit_package_dir,
        'config', 'moveit_planning_adapters.yaml'
    )
    
    # Load YAML files
    def load_yaml(file_path):
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    
    # Declare launch arguments
    launch_arguments = [
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time'
        ),
        DeclareLaunchArgument(
            'rviz',
            default_value='true',
            description='Launch RViz'
        ),
    ]
    
    use_sim_time = LaunchConfiguration('use_sim_time')
    rviz_arg = LaunchConfiguration('rviz')
    
    # Move Group Server
    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            {'robot_description': open(urdf_file).read()},
            {'robot_description_semantic': open(srdf_file).read()},
            load_yaml(kinematics_yaml),
            load_yaml(joint_limits_yaml),
            load_yaml(moveit_planning_adapters_yaml),
            {'use_sim_time': use_sim_time},
        ],
        arguments=['--ros-args', '--log-level', 'INFO'],
    )
    
    # RViz Node with MoveIt2 configuration
    rviz_config_dir = os.path.join(
        w10_moveit_package_dir,
        'config'
    )
    
    rviz_config_file = os.path.join(rviz_config_dir, 'moveit.rviz')
    
    # Check if custom rviz config exists, otherwise use default
    if not os.path.exists(rviz_config_file):
        rviz_config_file = ''
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file] if rviz_config_file else [],
        parameters=[
            {'use_sim_time': use_sim_time},
        ],
        condition=ExecuteProcess(
            cmd=['test', '-n', rviz_arg]
        ) if rviz_arg else None,
    )
    
    # State Publisher Node
    state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': open(urdf_file).read()},
            {'use_sim_time': use_sim_time},
        ],
    )
    
    # Static Transform Publisher (for base_link)
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['--frame-id', 'world', '--child-frame-id', 'base_link',
                   '--x', '0', '--y', '0', '--z', '0'],
        output='screen',
    )
    
    ld = LaunchDescription()
    
    # Add all launch arguments
    for arg in launch_arguments:
        ld.add_action(arg)
    
    # Add nodes
    ld.add_action(state_publisher_node)
    ld.add_action(static_tf_node)
    ld.add_action(move_group_node)
    
    # Conditionally add RViz
    if os.environ.get('DISPLAY'):
        ld.add_action(rviz_node)
    
    return ld
