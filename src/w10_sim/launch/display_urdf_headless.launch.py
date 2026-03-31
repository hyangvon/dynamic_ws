#!/usr/bin/env python3
"""
w10机械臂可视化 - Headless版本（需远程RViz连接）
或使用joint_state_publisher而非GUI版本
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    
    # 获取w10_sim包的路径
    w10_sim_dir = FindPackageShare('w10_sim')
    
    # 声明URDF文件参数
    urdf_model_arg = DeclareLaunchArgument(
        'model',
        default_value=PathJoinSubstitution([w10_sim_dir, 'urdf', 'w10_canonical.urdf']),
        description='URDF模型文件路径'
    )
    
    urdf_model_path = LaunchConfiguration('model')
    
    # 使用Command读取URDF文件
    urdf_content = Command(['cat ', urdf_model_path])
    
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
        urdf_model_arg,
        robot_state_publisher_node,
        joint_state_publisher_node,
    ])
