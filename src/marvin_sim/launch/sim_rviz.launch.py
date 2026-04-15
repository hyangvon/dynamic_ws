#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_dir = get_package_share_directory('marvin_sim')
    default_urdf = os.path.join(pkg_dir, 'urdf', 'marvin_body.urdf')
    default_params = os.path.join(pkg_dir, 'config', 'vi_params.yaml')

    urdf_arg = DeclareLaunchArgument(
        'urdf_file',
        default_value=default_urdf,
        description='Path to the URDF file',
    )
    params_arg = DeclareLaunchArgument(
        'params_file',
        default_value=default_params,
        description='Path to the simulation params yaml',
    )

    def launch_setup(context, *args, **kwargs):
        urdf_path = context.launch_configurations['urdf_file']
        params_path = context.launch_configurations['params_file']
        with open(urdf_path, 'r') as f:
            urdf_content = f.read()

        return [
            # 将 URDF 的 TF 树发布出来
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                output='screen',
                parameters=[{'robot_description': urdf_content}],
            ),
            # 运行变分积分器仿真，实时发布 /joint_states
            Node(
                package='marvin_sim',
                executable='ctsvi_node',
                output='screen',
                parameters=[params_path],
            ),
            # 启动 RViz2 可视化
            Node(
                package='rviz2',
                executable='rviz2',
                output='screen',
            ),
        ]

    return LaunchDescription([
        urdf_arg,
        params_arg,
        OpaqueFunction(function=launch_setup),
    ])
