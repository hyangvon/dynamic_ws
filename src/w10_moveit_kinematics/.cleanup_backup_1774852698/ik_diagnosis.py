#!/usr/bin/env python3
"""Deep IK solver diagnosis script"""

import rclpy
import json
from moveit_msgs.srv import GetPositionIK, GetPositionFK
from moveit_msgs.msg import RobotState, MoveItErrorCodes
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped, Point, Quaternion

def diagnose_ik():
    rclpy.init()
    node = rclpy.create_node('ik_diagnostic')
    
    ik_client = node.create_client(GetPositionIK, '/compute_ik')
    fk_client = node.create_client(GetPositionFK, '/compute_fk')
    
    # Wait for services
    ik_client.wait_for_service(timeout_sec=2)
    fk_client.wait_for_service(timeout_sec=2)
    
    print("=" * 70)
    print("IK SOLVER DEEP DIAGNOSIS")
    print("=" * 70)
    
    # Test case 1: Home position (should be easiest)
    print("\n[TEST 1] Home Position (All joints at 0)")
    print("-" * 70)
    
    # First get FK for home position to verify
    fk_request = GetPositionFK.Request()
    fk_request.header.frame_id = 'base_link'
    fk_request.fk_link_names = ['Link8']
    
    robot_state = RobotState()
    joint_state = JointState()
    joint_state.name = ['joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
    joint_state.position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    robot_state.joint_state = joint_state
    fk_request.robot_state = robot_state
    
    fk_future = fk_client.call_async(fk_request)
    rclpy.spin_until_future_complete(node, fk_future, timeout_sec=5)
    fk_result = fk_future.result()
    
    print(f"FK Result (home):")
    if fk_result.pose_stamped:
        pose = fk_result.pose_stamped[0]
        print(f"  Position: X={pose.pose.position.x:.4f}, Y={pose.pose.position.y:.4f}, Z={pose.pose.position.z:.4f}")
        print(f"  Orientation: Qx={pose.pose.orientation.x:.4f}, Qy={pose.pose.orientation.y:.4f}, Qz={pose.pose.orientation.z:.4f}, Qw={pose.pose.orientation.w:.4f}")
        target_pose = pose
    else:
        print("  ERROR: No FK result returned")
        target_pose = None
    
    # Now try IK with different configurations
    print(f"\nTrying IK for home position...")
    
    configs_to_test = [
        {"name": "Default (timeout=5s)", "timeout_sec": 5, "attempts": 3},
        {"name": "Aggressive (timeout=2s)", "timeout_sec": 2, "attempts": 50},
        {"name": "Minimal (timeout=0.1s)", "timeout_sec": 0.1, "attempts": 1},
    ]
    
    if target_pose:
        for config in configs_to_test:
            print(f"\n  Config: {config['name']}")
            
            ik_request = GetPositionIK.Request()
            ik_request.ik_request.group_name = 'w10_arm'
            ik_request.ik_request.pose_stamped = target_pose
            ik_request.ik_request.ik_link_name = 'Link8'
            ik_request.ik_request.timeout.sec = int(config['timeout_sec'])
            ik_request.ik_request.timeout.nanosec = int((config['timeout_sec'] % 1) * 1e9)
            
            # Try with different initial states
            for init_config in [
                ("Zero", [0.0] * 7),
                ("Random", [0.3, -0.2, 0.5, -0.4, 0.1, -0.3, 0.2]),
            ]:
                robot_state = RobotState()
                joint_state = JointState()
                joint_state.name = ['joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
                joint_state.position = init_config[1]
                robot_state.joint_state = joint_state
                ik_request.ik_request.robot_state = robot_state
                
                ik_future = ik_client.call_async(ik_request)
                rclpy.spin_until_future_complete(node, ik_future, timeout_sec=6)
                ik_result = ik_future.result()
                
                error_code = ik_result.error_code.val
                error_name = get_error_name(error_code)
                
                print(f"    Initial: {init_config[0]:10s} | Error: {error_code:4d} ({error_name:25s})", end="")
                
                if error_code == 1:  # SUCCESS
                    solution = ik_result.solution.joint_state.position
                    print(f" | Solution: {[f'{x:.2f}' for x in solution]}")
                else:
                    print()
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)
    
    rclpy.shutdown()

def get_error_name(code):
    """Map error codes to names"""
    error_map = {
        1: "SUCCESS",
        -1: "FAILURE",
        -2: "PLANNING_FAILED",
        -3: "INVALID_MOTION_PLAN",
        -4: "MOTION_PLAN_INVALIDATED_BY_ENVIRONMENT_CHANGE",
        -5: "CONTROL_FAILED",
        -6: "UNABLE_TO_AQUIRE_SENSOR_DATA",
        -7: "TIMEOUT",
        -8: "UNINITIALIZED",
        -9: "GOAL_CONSTRAINTS_VIOLATED",
        -10: "GOAL_ORIENTATION_CONSTRAINT_VIOLATED",
        -11: "GOAL_POSITION_CONSTRAINT_VIOLATED",
        -12: "GOAL_CONSTRAINTS_VIOLATED",
        -13: "PATH_CONSTRAINTS_VIOLATED",
        -31: "NO_IK_SOLUTION",
    }
    return error_map.get(code, f"UNKNOWN_{code}")

if __name__ == '__main__':
    diagnose_ik()
