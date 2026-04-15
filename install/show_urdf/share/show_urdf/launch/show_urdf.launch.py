#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def generate_launch_description():
    urdf_arg = DeclareLaunchArgument(
        'urdf_file',
        description='Absolute path to the URDF file to display',
    )

    urdf_file = LaunchConfiguration('urdf_file')

    def load_urdf(context):
        path = context.launch_configurations['urdf_file']
        with open(path, 'r') as f:
            return f.read()

    from launch.actions import OpaqueFunction

    def launch_setup(context, *args, **kwargs):
        urdf_content = load_urdf(context)

        rsp_node = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': urdf_content}],
        )

        jsp_gui_node = Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            output='screen',
        )

        rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
        )

        return [rsp_node, jsp_gui_node, rviz_node]

    return LaunchDescription([
        urdf_arg,
        OpaqueFunction(function=launch_setup),
    ])
