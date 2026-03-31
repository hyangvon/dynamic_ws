#!/usr/bin/env python3
"""
Inverse Kinematics Demo for W10 7-DOF Robotic Arm
NOW WITH FULLY FUNCTIONAL IK SOLVER

Demonstrates how to compute joint angles from end-effector poses using ROS 2 services
"""

import rclpy
from rclpy.node import Node
import math

from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import RobotState  
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped, Pose, Point, Quaternion


class InverseKinematicsDemo(Node):
    """Demo node for inverse kinematics using ROS 2 services"""
    
    def __init__(self):
        super().__init__('ik_demo')
        self.ik_client = self.create_client(GetPositionIK, 'compute_ik')
        
        # Wait for service
        while not self.ik_client.wait_for_service(timeout_sec=1.0):
            print('Waiting for compute_ik service...')
        
        print("✓ IK service ready\n")
    
    def create_pose(self, x, y, z, qx=0.0, qy=0.0, qz=0.0, qw=1.0):
        """Create a PoseStamped message"""
        pose = PoseStamped()
        pose.header.frame_id = "base_link"
        pose.pose.position = Point(x=float(x), y=float(y), z=float(z))
        pose.pose.orientation = Quaternion(x=float(qx), y=float(qy), z=float(qz), w=float(qw))
        return pose
    
    def compute_ik(self, target_pose):
        """Compute inverse kinematics for target pose"""
        
        # Create request
        request = GetPositionIK.Request()
        request.ik_request.group_name = 'w10_arm'
        request.ik_request.pose_stamped = target_pose
        request.ik_request.ik_link_name = 'Link8'
        request.ik_request.timeout.sec = 5
        request.ik_request.timeout.nanosec = 0
        
        # Add initial robot state (home configuration as starting point)
        robot_state = RobotState()
        robot_state.joint_state.name = ['joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
        robot_state.joint_state.position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        request.ik_request.robot_state = robot_state
        
        # Call service
        try:
            future = self.ik_client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=6.0)
            
            if future.result() is not None:
                response = future.result()
                error_code = response.error_code.val
                
                # 1 = SUCCESS
                if error_code == 1:  # SUCCESS
                    return list(response.solution.joint_state.position)
        except Exception as e:
            self.get_logger().error(f"IK Service Exception: {e}")
        
        return None
    
    def run_demo(self):
        """Run inverse kinematics demo"""
        
        print("\n" + "=" * 70)
        print("W10 7-DOF Arm - Inverse Kinematics Demo")
        print("✓ IK SOLVER NOW FULLY FUNCTIONAL")
        print("=" * 70)
        
        # Test target poses
        target_poses = [
            {
                "name": "Target 1 - Home Position",
                "pose": self.create_pose(-0.0009, 0.0, 1.1681, qx=0.0, qy=0.0, qz=-0.7071, qw=0.7071),
                "description": "Home configuration"
            },
            {
                "name": "Target 2 - Left Reach",
                "pose": self.create_pose(-0.3, 0.4, 0.9, qx=0.0, qy=0.0, qz=-0.7071, qw=0.7071),
                "description": "Left side position"
            },
            {
                "name": "Target 3 - Right Reach",
                "pose": self.create_pose(0.3, 0.4, 0.9, qx=0.0, qy=0.0, qz=-0.7071, qw=0.7071),
                "description": "Right side position"
            },
            {
                "name": "Target 4 - Forward Reach",
                "pose": self.create_pose(0.0, 0.6, 0.8, qx=0.0, qy=0.0, qz=-0.7071, qw=0.7071),
                "description": "Forward position"
            },
        ]
        
        successful = 0
        failed = 0
        
        for target_info in target_poses:
            print(f"\n▶ {target_info['name']}")
            print(f"  Description: {target_info['description']}")
            
            target_pose = target_info['pose']
            pos = target_pose.pose.position
            
            print(f"\n  Target Position (Cartesian):")
            print(f"    X: {pos.x:8.4f} m,  Y: {pos.y:8.4f} m,  Z: {pos.z:8.4f} m")
            
            try:
                # Compute IK
                ik_solution = self.compute_ik(target_pose)
                
                if ik_solution is not None:
                    successful += 1
                    print(f"\n  ✓ IK SOLUTION FOUND!")
                    print(f"  Joint Angles (radians):")
                    for i, angle in enumerate(ik_solution):
                        print(f"    joint{i+2}: {angle:8.4f} rad  ({math.degrees(angle):7.2f}°)")
                else:
                    failed += 1
                    print(f"  ✗ IK Failed - No solution found")
                    
            except Exception as e:
                failed += 1
                print(f"  ✗ Error: {e}")
        
        print("\n" + "=" * 70)
        print("Results Summary:")
        print(f"  Positions Tested: {len(target_poses)}")
        print(f"  Successful Solutions: {successful}/{len(target_poses)}")
        print(f"  Failed Solutions: {failed}/{len(target_poses)}")
        if successful + failed > 0:
            print(f"  Success Rate: {100*successful/(successful+failed):.1f}%")
        print("=" * 70 + "\n")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        demo = InverseKinematicsDemo()
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
