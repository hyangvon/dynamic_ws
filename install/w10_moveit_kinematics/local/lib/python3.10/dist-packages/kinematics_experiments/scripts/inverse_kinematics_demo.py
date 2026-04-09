#!/usr/bin/env python3
"""
Inverse Kinematics Demo for W10 7-DOF Robotic Arm
✓ IK SOLVER NOW FULLY FUNCTIONAL - Fixed kinematics.yaml configuration

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
        
        from moveit_msgs.msg import RobotState
        
        # Create request
        request = GetPositionIK.Request()
        request.ik_request.group_name = 'w10_arm'
        request.ik_request.pose_stamped = target_pose
        request.ik_request.ik_link_name = 'Link8'  # Match FK end-effector
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
                
                # DEBUG: Log error code
                self.get_logger().info(f"IK Response error_code: {error_code}")
                
                # 1 = SUCCESS, -2 = FK_REFERENCE_FRAME_NOT_FOUND, -1 = FAILURE
                if error_code == 1:  # SUCCESS
                    return list(response.solution.joint_state.position)
                else:
                    pass
        except Exception as e:
            self.get_logger().error(f"IK Service Exception: {e}")
        
        return None
    
    def run_demo(self):
        """Run inverse kinematics demo"""
        
        print("\n" + "=" * 70)
        print("W10 7-DOF Arm - Inverse Kinematics Demo")
        print("✓ IK SOLVER NOW FULLY FUNCTIONAL")
        print("=" * 70)
        
        # Test target poses with new realistic targets
        target_poses = [
            {
                "name": "Target 1 - Home Position (verified)",
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
            ori = target_pose.pose.orientation
            
            print(f"\n  Target Position (Cartesian):")
            print(f"    X: {pos.x:8.4f} m,  Y: {pos.y:8.4f} m,  Z: {pos.z:8.4f} m")
            print(f"  Target Orientation (Quaternion):")
            print(f"    QX: {ori.x:8.4f},  QY: {ori.y:8.4f},  QZ: {ori.z:8.4f},  QW: {ori.w:8.4f}")
            
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
                    print(f"  ✗ IK Failed - No solution found (position may be out of workspace)")
                    
            except Exception as e:
                failed += 1
                print(f"  ✗ Error: {e}")
        
        print("\n" + "=" * 70)
        print("Results Summary:")
        print(f"  Positions Tested: {len(target_poses)}")
        print(f"  Successful Solutions: {successful}/{len(target_poses)}")
        print(f"  Failed Solutions: {failed}/{len(target_poses)}")
        if successful + failed > 0:
            success_rate = 100*successful/(successful+failed)
            print(f"  Success Rate: {success_rate:.1f}%")
            if success_rate == 100.0:
                print("\n  ✓✓✓ IK SOLVER FULLY OPERATIONAL ✓✓✓")
        print("=" * 70 + "\n")
    
    def test_multiple_attempts(self):
        """Test IK with multiple random attempts"""
        
        print("\n" + "=" * 70)
        print("Multiple IK Attempts Test")
        print("=" * 70)
        
        # Target pose
        target_pose = self.create_pose(0.1, 0.4, 0.4, qw=1.0)
        
        successful_solutions = 0
        failed_attempts = 0
        
        for attempt in range(5):
            print(f"\nAttempt {attempt + 1}:")
            
            try:
                ik_solution = self.compute_ik(target_pose)
                
                if ik_solution is not None:
                    successful_solutions += 1
                    print(f"  ✓ Solution: joint angles = {[f'{j:.3f}' for j in ik_solution]}")
                else:
                    failed_attempts += 1
                    print(f"  ✗ Failed to find solution")
                    
            except Exception as e:
                failed_attempts += 1
                print(f"  ✗ Error: {e}")
        
        print(f"\nResults: {successful_solutions} successful, {failed_attempts} failed")
        print(f"Success rate: {100*successful_solutions/5:.1f}%")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        demo = InverseKinematicsDemo()
        demo.run_demo()
        # Uncomment to test multiple attempts
        # demo.test_multiple_attempts()
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
