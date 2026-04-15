#!/usr/bin/env python3
"""
从 CSV 数据回放机械臂姿态并在 RViz2 中可视化。

用法：
    ros2 launch marvin_sim replay_rviz.launch.py
    ros2 launch marvin_sim replay_rviz.launch.py csv_path:=src/marvin_sim/csv/q0_dt0p01_T10_a0p4_b0p04/ctsvi_ad/
    ros2 launch marvin_sim replay_rviz.launch.py speed:=2.0 loop:=true
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_dir = get_package_share_directory('marvin_sim')
    default_urdf = os.path.join(pkg_dir, 'urdf', 'marvin_body.urdf')

    return LaunchDescription([
        DeclareLaunchArgument('urdf_file',   default_value=default_urdf,  description='URDF 路径'),
        DeclareLaunchArgument('csv_path',    default_value='',            description='CSV 目录（空=自动选最新）'),
        DeclareLaunchArgument('speed',       default_value='1.0',         description='回放倍速'),
        DeclareLaunchArgument('loop',        default_value='false',       description='是否循环播放'),
        OpaqueFunction(function=_launch_setup),
    ])


def _launch_setup(context, *args, **kwargs):
    urdf_path = context.launch_configurations['urdf_file']
    csv_path  = context.launch_configurations['csv_path']
    speed     = context.launch_configurations['speed']
    loop      = context.launch_configurations['loop']

    with open(urdf_path, 'r') as f:
        urdf_content = f.read()

    replay_args = ['--speed', speed]
    if loop.lower() in ('true', '1', 'yes'):
        replay_args.append('--loop')
    if csv_path:
        replay_args += ['--path', csv_path]

    return [
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': urdf_content}],
        ),
        Node(
            package='marvin_sim',
            executable='replay_rviz.py',
            output='screen',
            arguments=replay_args,
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
        ),
    ]
