#!/usr/bin/env python3
"""
w10机械臂URDF可视化launch文件
使用robot_state_publisher将URDF发布到TF树，RViz中可视化显示
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    
    # 获取w10_sim包的路径
    w10_sim_dir = FindPackageShare('w10_sim')
    
    # 声明URDF文件参数
    urdf_model_arg = DeclareLaunchArgument(
        'model',
        default_value=PathJoinSubstitution([w10_sim_dir, 'urdf', 'w10_canonical.urdf']),
        description='URDF模型文件路径 (支持 w10_canonical.urdf 或 w10.urdf)'
    )
    
    urdf_model_path = LaunchConfiguration('model')
    
    # 使用Command读取URDF文件
    urdf_content = Command(['cat ', urdf_model_path])
    
    # 启动robot_state_publisher节点（发布URDF和TF变换）
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': urdf_content,
            'use_sim_time': False,  # 不使用仿真时间
        }],
    )
    
    # 启动joint_state_publisher GUI（手动控制关节）
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
    )
    
    # 启动RViz
    rviz_config_path = PathJoinSubstitution([w10_sim_dir, 'rviz', 'w10.rviz'])
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
    )
    
    return LaunchDescription([
        urdf_model_arg,
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz_node,
    ])
