#!/usr/bin/env python3
"""
w10机械臂URDF可视化launch文件
使用robot_state_publisher将URDF发布到TF树，RViz中可视化显示
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    
    # 直接读取URDF文件内容
    # urdf_file = os.path.join(
    #     os.path.dirname(__file__), 
    #     '..', 'urdf', 'w10_canonical.urdf'
    # )
    
    urdf_file = os.path.join(
        os.path.dirname(__file__), 
        '..', 'urdf', 'w10new.urdf'
    )
    
    with open(urdf_file, 'r') as f:
        urdf_content = f.read()
    
    # 获取w10_sim包的路径
    w10_sim_dir = FindPackageShare('w10_sim')
    
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
    # rviz_config_path = PathJoinSubstitution([w10_sim_dir, 'rviz', 'w10.rviz'])
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        # arguments=['-d', rviz_config_path],
    )
    
    return LaunchDescription([
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz_node,
    ])
