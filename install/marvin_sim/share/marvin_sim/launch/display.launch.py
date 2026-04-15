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

    urdf_arg = DeclareLaunchArgument(
        'urdf_file',
        default_value=default_urdf,
        description='Path to the URDF file',
    )

    def launch_setup(context, *args, **kwargs):
        urdf_path = context.launch_configurations['urdf_file']
        with open(urdf_path, 'r') as f:
            urdf_content = f.read()

        return [
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                output='screen',
                parameters=[{'robot_description': urdf_content}],
            ),
            Node(
                package='joint_state_publisher_gui',
                executable='joint_state_publisher_gui',
                output='screen',
            ),
            Node(
                package='rviz2',
                executable='rviz2',
                output='screen',
            ),
        ]

    return LaunchDescription([
        urdf_arg,
        OpaqueFunction(function=launch_setup),
    ])
