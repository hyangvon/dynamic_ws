"""
Simplified launch file for W10 MoveIt2 kinematics demos
Useful for testing without full RViz setup
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import yaml


def generate_launch_description():
    """Generate simplified launch description"""
    
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
    
    # Move Group Server (minimal)
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
        ],
    )
    
    # State Publisher Node
    state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': open(urdf_file).read()},
        ],
    )
    
    # Static Transform Publisher
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['--frame-id', 'world', '--child-frame-id', 'base_link',
                   '--x', '0', '--y', '0', '--z', '0'],
        output='screen',
    )
    
    # Joint State Publisher - publishes default joint states for TF tree
    joint_state_pub_node = Node(
        package='w10_moveit_kinematics',
        executable='joint_state_publisher.py',
        output='screen',
    )
    
    ld = LaunchDescription()
    
    # Add nodes (no RViz)
    ld.add_action(joint_state_pub_node)  # Add joint state publisher first
    ld.add_action(state_publisher_node)
    ld.add_action(static_tf_node)
    ld.add_action(move_group_node)
    
    return ld
