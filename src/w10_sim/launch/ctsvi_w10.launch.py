#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Get the package directory
    pkg_dir = FindPackageShare(package='w10_sim').find('w10_sim')
    config_file = os.path.join(pkg_dir, 'config', 'vi_params.yaml')

    # Create the node
    ctsvi_w10_node = Node(
        package='w10_sim',
        executable='ctsvi_w10_node',
        name='ctsvi_w10_node',
        output='screen',
        parameters=[config_file],
    )

    return LaunchDescription([
        ctsvi_w10_node,
    ])
