#!/usr/bin/env python3
"""
w10机械臂可视化 - Headless版本（需远程RViz连接）
或使用joint_state_publisher而非GUI版本
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, TextSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    
    # 直接读取URDF文件内容
    urdf_file = os.path.join(
        os.path.dirname(__file__), 
        '..', 'urdf', 'w10_canonical.urdf'
    )
    
    with open(urdf_file, 'r') as f:
        urdf_content = f.read()
    
    # robot_state_publisher节点
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': urdf_content,
            'use_sim_time': False,
        }],
    )
    
    # joint_state_publisher节点（不用GUI，发布固定关节角度）
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': False,
        }],
    )
    
    return LaunchDescription([
        robot_state_publisher_node,
        joint_state_publisher_node,
    ])
