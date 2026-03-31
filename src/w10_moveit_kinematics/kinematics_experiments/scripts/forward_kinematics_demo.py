#!/usr/bin/env python3
"""
Forward Kinematics Demo for W10 7-DOF Robotic Arm

Demonstrates how to compute end-effector poses from joint angles using ROS 2 services
"""

import rclpy
from rclpy.node import Node
import math
import sys
import time

from moveit_msgs.srv import GetPositionFK
from moveit_msgs.msg import RobotState
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped
import numpy as np


class ForwardKinematicsDemo(Node):
    """Demo node for forward kinematics using ROS 2 services"""
    
    def __init__(self):
        super().__init__('fk_demo')
        self.fk_client = self.create_client(GetPositionFK, 'compute_fk')
        
        # Wait for service
        while not self.fk_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for compute_fk service...')
        
        self.get_logger().info("FK service ready")
    
    def compute_fk(self, joint_angles):
        """Compute forward kinematics for given joint angles"""
        
        # Create request
        request = GetPositionFK.Request()
        request.header.frame_id = 'base_link'
        request.fk_link_names = ['Link8']  # End-effector link
        
        # Create robot state with joint positions
        robot_state = RobotState()
        joint_state = JointState()
        joint_state.name = ['joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
        joint_state.position = joint_angles
        robot_state.joint_state = joint_state
        
        request.robot_state = robot_state
        
        # Call service
        future = self.fk_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            response = future.result()
            if response.pose_stamped:
                return response.pose_stamped[0]
        
        return None
    
    def run_demo(self):
        """Run forward kinematics demo"""
        
        print("\n" + "=" * 70)
        print("W10 7-DOF Arm - Forward Kinematics Demo")
        print("=" * 70)
        
        # Test cases: different joint configurations
        test_configs = [
            {
                "name": "Home Position",
                "joints": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            },
            {
                "name": "Configuration 1",
                "joints": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
            },
            {
                "name": "Configuration 2", 
                "joints": [-0.5, -0.5, 0.3, 0.0, -0.3, 0.5, 0.0]
            },
            {
                "name": "Configuration 3",
                "joints": [math.pi/4, -0.3, 0.8, -0.2, 0.5, -0.3, 0.0]
            }
        ]
        
        for config in test_configs:
            print(f"\n▶ {config['name']}")
            print(f"  Joint Angles: {[f'{v:.4f}' for v in config['joints']]}")
            
            try:
                # Compute FK
                pose = self.compute_fk(config['joints'])
                
                if pose is None:
                    print("  ✗ FK computation failed")
                    continue
                
                pos = pose.pose.position
                orn = pose.pose.orientation
                
                print(f"\n  End-Effector Position (Cartesian):")
                print(f"    X: {pos.x:8.4f} m")
                print(f"    Y: {pos.y:8.4f} m")
                print(f"    Z: {pos.z:8.4f} m")
                
                print(f"\n  End-Effector Orientation (Quaternion):")
                print(f"    QX: {orn.x:8.4f}")
                print(f"    QY: {orn.y:8.4f}")
                print(f"    QZ: {orn.z:8.4f}")
                print(f"    QW: {orn.w:8.4f}")
                
                # Compute RPY from quaternion
                roll, pitch, yaw = self._quaternion_to_rpy(orn)
                print(f"\n  End-Effector Orientation (RPY):")
                print(f"    Roll:  {roll:8.4f} rad  ({math.degrees(roll):7.2f}°)")
                print(f"    Pitch: {pitch:8.4f} rad  ({math.degrees(pitch):7.2f}°)")
                print(f"    Yaw:   {yaw:8.4f} rad  ({math.degrees(yaw):7.2f}°)")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        print("\n" + "=" * 70)
        print("Forward Kinematics Demo Completed Successfully ✓")
        print("=" * 70 + "\n")
    
    @staticmethod
    def _quaternion_to_rpy(quaternion):
        """Convert quaternion to roll, pitch, yaw"""
        
        x = quaternion.x
        y = quaternion.y
        z = quaternion.z
        w = quaternion.w
        
        # Roll (rotation around X-axis)
        roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
        
        # Pitch (rotation around Y-axis)
        sin_pitch = 2 * (w * y - z * x)
        sin_pitch = max(-1, min(1, sin_pitch))  # Clamp to [-1, 1]
        pitch = math.asin(sin_pitch)
        
        # Yaw (rotation around Z-axis)
        yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        
        return roll, pitch, yaw


def main(args=None):
    rclpy.init(args=args)
    
    try:
        demo = ForwardKinematicsDemo()
        demo.run_demo()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
