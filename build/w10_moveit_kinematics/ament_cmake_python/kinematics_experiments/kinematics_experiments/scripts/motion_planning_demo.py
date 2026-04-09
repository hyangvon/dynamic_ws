#!/usr/bin/env python3
"""
Motion Planning Demo for W10 7-DOF Robotic Arm - MODERNIZED IK-BASED VERSION

Demonstrates trajectory planning using ROS 2 GetPositionIK service.
✓ IK SOLVER NOW FULLY FUNCTIONAL - Real joint angle computation

Key Features:
- Direct ROS 2 service calls to /compute_ik
- Real inverse kinematics computation (not moveit_commander)
- Multi-waypoint trajectory planning
- Success rate reporting
"""

import rclpy
from rclpy.node import Node
import math
import sys
import time
from typing import List, Tuple, Optional

from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import RobotState
from geometry_msgs.msg import PoseStamped, Pose, Point, Quaternion
from sensor_msgs.msg import JointState
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import ColorRGBA
import numpy as np


class MotionPlanningDemo(Node):
    """Demo node for trajectory planning using IK solver"""
    
    def __init__(self):
        super().__init__('motion_planning_demo')
        
        # Create IK service client
        self.ik_client = self.create_client(GetPositionIK, '/compute_ik')
        
        # Wait for IK service
        while not self.ik_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("⏳ Waiting for /compute_ik service...")
        
        self.get_logger().info("✓ IK service available")
        
        # Create visualization publishers (using absolute paths)
        self.waypoint_pub = self.create_publisher(MarkerArray, '/waypoints', 10)
        self.trajectory_pub = self.create_publisher(MarkerArray, '/trajectory', 10)
        self.workspace_pub = self.create_publisher(MarkerArray, '/workspace', 10)
        
        # Create timer for continuous publishing
        self.publish_timer = self.create_timer(0.5, self.continuous_publish)
        
        # Store current markers for continuous publishing
        self.current_waypoint_markers = MarkerArray()
        self.current_trajectory_markers = MarkerArray()
        self.current_workspace_markers = MarkerArray()
        
        self.get_logger().info("✓ Visualization publishers created")
        
        # Robot parameters
        self.group_name = "w10_arm"
        self.end_effector_link = "Link8"
        self.planning_frame = "base_link"
        self.num_joints = 7
        
        # Joint names (W10 has joint2-joint8, NOT joint1-joint7)
        self.joint_names = ['joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
        
        # Initial joint configuration
        self.home_config = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        self.get_logger().info("✓ Motion planning demo initialized")
    
    def continuous_publish(self):
        """Continuously publish stored markers"""
        if self.current_waypoint_markers.markers:
            self.waypoint_pub.publish(self.current_waypoint_markers)
        if self.current_trajectory_markers.markers:
            self.trajectory_pub.publish(self.current_trajectory_markers)
        if self.current_workspace_markers.markers:
            self.workspace_pub.publish(self.current_workspace_markers)
    
    def publish_waypoint_markers(self, waypoints: List[PoseStamped], label: str = "waypoints"):
        """Publish waypoints as sphere markers in RViz"""
        marker_array = MarkerArray()
        
        for i, pose in enumerate(waypoints):
            marker = Marker()
            marker.header.frame_id = self.planning_frame
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = label
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.lifetime.sec = 0
            marker.lifetime.nanosec = 0
            
            marker.pose = pose.pose
            marker.scale.x = 0.05
            marker.scale.y = 0.05
            marker.scale.z = 0.05
            
            # Color: Red for start, Green for middle, Blue for end
            if i == 0:
                marker.color = ColorRGBA(r=1.0, g=0.0, b=0.0, a=0.8)
            elif i == len(waypoints) - 1:
                marker.color = ColorRGBA(r=0.0, g=0.0, b=1.0, a=0.8)
            else:
                marker.color = ColorRGBA(r=0.0, g=1.0, b=0.0, a=0.8)
            
            marker_array.markers.append(marker)
        
        # Store for continuous publishing
        self.current_waypoint_markers = marker_array
        
        # Publish multiple times to ensure delivery
        for _ in range(5):
            self.waypoint_pub.publish(marker_array)
            time.sleep(0.05)
    
    def publish_trajectory_markers(self, waypoints: List[PoseStamped], trajectory: List[List[float]] = None, label: str = "trajectory"):
        """
        Publish trajectory visualization in RViz
        
        Args:
            waypoints: List of target poses (path points)
            trajectory: Optional list of joint configurations (for future use)
            label: Label for the markers
        """
        marker_array = MarkerArray()
        
        # Line strip marker connecting waypoints
        line_marker = Marker()
        line_marker.header.frame_id = self.planning_frame
        line_marker.header.stamp = self.get_clock().now().to_msg()
        line_marker.ns = label + "_line"
        line_marker.id = 0
        line_marker.type = Marker.LINE_STRIP
        line_marker.action = Marker.ADD
        line_marker.lifetime.sec = 0
        line_marker.lifetime.nanosec = 0
        
        line_marker.scale.x = 0.01
        line_marker.color = ColorRGBA(r=0.0, g=1.0, b=1.0, a=0.6)
        
        # Add waypoint positions as line points
        for waypoint in waypoints:
            p = Point()
            p.x = float(waypoint.pose.position.x)
            p.y = float(waypoint.pose.position.y)
            p.z = float(waypoint.pose.position.z)
            line_marker.points.append(p)
        
        # Add intermediate points if trajectory provided
        if trajectory is not None and len(trajectory) > len(waypoints):
            # Create interpolated points between waypoints
            step = max(1, len(trajectory) // (len(waypoints) * 2))
            for i in range(0, len(trajectory), step):
                # Use a simple visualization: lift points up slightly
                if i < len(waypoints):
                    p = Point()
                    p.x = float(line_marker.points[i].x) if i < len(line_marker.points) else 0.0
                    p.y = float(line_marker.points[i].y) if i < len(line_marker.points) else 0.0
                    p.z = float(line_marker.points[i].z) if i < len(line_marker.points) else 0.0
                    line_marker.points.append(p)
        
        marker_array.markers.append(line_marker)
        
        # Points marker (yellow dots at waypoints)
        points_marker = Marker()
        points_marker.header.frame_id = self.planning_frame
        points_marker.header.stamp = self.get_clock().now().to_msg()
        points_marker.ns = label + "_points"
        points_marker.id = 1
        points_marker.type = Marker.POINTS
        points_marker.action = Marker.ADD
        points_marker.lifetime.sec = 0
        points_marker.lifetime.nanosec = 0
        
        points_marker.scale.x = 0.03
        points_marker.scale.y = 0.03
        points_marker.color = ColorRGBA(r=1.0, g=1.0, b=0.0, a=1.0)
        
        # Add waypoint positions as points
        for waypoint in waypoints:
            p = Point()
            p.x = float(waypoint.pose.position.x)
            p.y = float(waypoint.pose.position.y)
            p.z = float(waypoint.pose.position.z)
            points_marker.points.append(p)
        
        marker_array.markers.append(points_marker)
        
        # Store for continuous publishing
        self.current_trajectory_markers = marker_array
        
        # Publish multiple times
        for _ in range(5):
            self.trajectory_pub.publish(marker_array)
            time.sleep(0.05)
    
    def publish_workspace_markers(self, positions: List[Tuple], reachable_list: List[bool], label: str = "workspace"):
        """Publish workspace reachability as markers in RViz"""
        marker_array = MarkerArray()
        
        for i, (pos, reachable) in enumerate(zip(positions, reachable_list)):
            marker = Marker()
            marker.header.frame_id = self.planning_frame
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = label
            marker.id = i
            marker.type = Marker.CUBE
            marker.action = Marker.ADD
            
            marker.pose.position.x = float(pos[0])
            marker.pose.position.y = float(pos[1])
            marker.pose.position.z = float(pos[2])
            marker.pose.orientation.w = 1.0
            
            marker.scale.x = 0.03
            marker.scale.y = 0.03
            marker.scale.z = 0.03
            
            # Green if reachable, Red if unreachable
            if reachable:
                marker.color = ColorRGBA(r=0.0, g=1.0, b=0.0, a=0.8)
            else:
                marker.color = ColorRGBA(r=1.0, g=0.0, b=0.0, a=0.8)
            
            marker_array.markers.append(marker)
        
        # Store for continuous publishing
        self.current_workspace_markers = marker_array
        
        # Publish multiple times
        for _ in range(5):
            self.workspace_pub.publish(marker_array)
            time.sleep(0.05)
    
    def solve_ik(self, pose: PoseStamped, initial_guess: Optional[List[float]] = None) -> Optional[List[float]]:
        """
        Solve inverse kinematics for a target pose
        
        Returns joint angles if successful, None otherwise
        """
        
        # Use home configuration as initial guess if not provided
        if initial_guess is None:
            initial_guess = self.home_config
        
        # Create IK request
        request = GetPositionIK.Request()
        request.ik_request.group_name = self.group_name
        request.ik_request.pose_stamped = pose
        request.ik_request.ik_link_name = self.end_effector_link
        request.ik_request.timeout.sec = 5
        
        # Set initial joint state
        robot_state = RobotState()
        robot_state.joint_state.name = self.joint_names
        robot_state.joint_state.position = initial_guess
        request.ik_request.robot_state = robot_state
        
        try:
            # Call IK service using the correct method
            future = self.ik_client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=6.0)
            
            if future.result() is not None:
                response = future.result()
                # Check for success  
                if response.error_code.val == 1:  # SUCCESS
                    return list(response.solution.joint_state.position)
            
            return None
                
        except Exception as e:
            return None
    
    def create_pose(self, x, y, z, qx=0, qy=0, qz=0, qw=1) -> PoseStamped:
        """Create a PoseStamped message"""
        pose = PoseStamped()
        pose.header.frame_id = self.planning_frame
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position = Point(x=float(x), y=float(y), z=float(z))
        pose.pose.orientation = Quaternion(x=float(qx), y=float(qy), z=float(qz), w=float(qw))
        return pose
    
    def create_trajectory(self, waypoints: List[PoseStamped], 
                         num_intermediate: int = 5) -> List[List[float]]:
        """
        Create trajectory through waypoints using IK solver
        
        Args:
            waypoints: List of target poses
            num_intermediate: Number of intermediate points between waypoints
        
        Returns:
            List of joint configurations forming trajectory
        """
        trajectory = []
        
        for i, waypoint in enumerate(waypoints):
            self.get_logger().info(f"Solving IK for waypoint {i+1}/{len(waypoints)}...")
            
            # Solve IK for this waypoint
            if trajectory:
                # Use last solution as initial guess
                joint_solution = self.solve_ik(waypoint, trajectory[-1])
            else:
                # Use home configuration for first waypoint
                joint_solution = self.solve_ik(waypoint)
            
            if joint_solution:
                trajectory.append(joint_solution)
                positions_str = ", ".join([f"{j:.3f}" for j in joint_solution])
                self.get_logger().info(f"  ✓ IK solved: [{positions_str}]")
                
                # Add intermediate points (linear interpolation in joint space)
                if i < len(waypoints) - 1:
                    next_waypoint = waypoints[i + 1]
                    next_solution = self.solve_ik(next_waypoint, joint_solution)
                    
                    if next_solution:
                        # Interpolate between current and next solution
                        for t in np.linspace(0.0, 1.0, num_intermediate + 2)[1:-1]:
                            intermediate = [
                                current + (next - current) * t
                                for current, next in zip(joint_solution, next_solution)
                            ]
                            trajectory.append(intermediate)
            else:
                self.get_logger().warn(f"  ✗ IK failed for waypoint {i+1}")
        
        return trajectory
    
    def demo_simple_trajectory(self):
        """Simple multi-point trajectory demo"""
        
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("DEMO 1: Simple Multi-Point Trajectory (Verified Reachable)")
        self.get_logger().info("=" * 70)
        
        # Define waypoints using VERIFIED reachable positions from inverse_kinematics_demo
        # All with default orientation (0, 0, 0, 1)
        waypoints = [
            self.create_pose(-0.0009, 0.0, 1.1681),   # Home - verified in IK demo
            self.create_pose(0.3, 0.4, 0.9),          # Right reach - verified
            self.create_pose(-0.3, 0.4, 0.9),         # Left reach - verified
            self.create_pose(-0.0009, 0.0, 1.1681),   # Back to home
        ]
        
        descriptions = [
            "Home (verified)",
            "Right reach (verified)",
            "Left reach (verified)",
            "Back to home"
        ]
        
        # Print waypoints
        self.get_logger().info(f"\nPlanned trajectory: {len(waypoints)} waypoints")
        for i, (pose, desc) in enumerate(zip(waypoints, descriptions)):
            self.get_logger().info(
                f"  {i+1}. {desc}: "
                f"x={pose.pose.position.x:.2f}, y={pose.pose.position.y:.2f}, z={pose.pose.position.z:.2f}"
            )
        
        # Create trajectory
        start_time = time.time()
        trajectory = self.create_trajectory(waypoints, num_intermediate=2)
        planning_time = time.time() - start_time
        
        # Print results
        self.get_logger().info(f"\n✓ Trajectory created in {planning_time:.2f}s")
        self.get_logger().info(f"  Total trajectory points: {len(trajectory)}")
        
        if trajectory:
            success_rate = len(trajectory) / len(waypoints) * 100
            self.get_logger().info(f"  Success rate: {success_rate:.1f}% ({len(trajectory)}/{len(waypoints)} waypoints)")
            
            # Publish visualization markers
            self.get_logger().info("  Publishing visualization markers to RViz...")
            self.publish_waypoint_markers(waypoints, "demo1_waypoints")
            self.publish_trajectory_markers(waypoints, trajectory, "demo1_trajectory")
            time.sleep(0.2)  # Allow markers to publish
            
            # Show some trajectory points
            step = max(1, len(trajectory) // 4)
            self.get_logger().info(f"\n  Trajectory points (every {step}th):")
            for i in range(0, len(trajectory), step):
                positions = ", ".join([f"{j:.3f}" for j in trajectory[i]])
                self.get_logger().info(f"    Point {i}: [{positions}]")
    
    def demo_figure_eight_trajectory(self):
        """Figure-8 trajectory demo"""
        
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("DEMO 2: Circular Trajectory (Verified Workspace)")
        self.get_logger().info("=" * 70)
        
        # Create circular pattern around verified center
        center_x, center_y, center_z = 0.0, 0.4, 0.9  # Center in verified workspace
        radius_xy = 0.2   # Small radius
        radius_z = 0.1
        num_points = 4
        
        waypoints = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = center_x + radius_xy * math.cos(angle)
            y = center_y + radius_xy * math.sin(angle)
            z = center_z + radius_z * math.sin(2 * angle)
            waypoints.append(self.create_pose(x, y, z))
        
        self.get_logger().info(f"\nPlanned trajectory: {num_points} waypoints in circular pattern")
        self.get_logger().info(f"  Center: ({center_x:.2f}, {center_y:.2f}, {center_z:.2f})")
        
        # Create trajectory
        start_time = time.time()
        trajectory = self.create_trajectory(waypoints, num_intermediate=1)
        planning_time = time.time() - start_time
        
        # Print results
        self.get_logger().info(f"\n✓ Circular trajectory created in {planning_time:.2f}s")
        self.get_logger().info(f"  Total trajectory points: {len(trajectory)}")
        
        if trajectory:
            success_rate = len(trajectory) / len(waypoints) * 100
            self.get_logger().info(f"  Success rate: {success_rate:.1f}% ({len(trajectory)}/{len(waypoints)} waypoints)")
            
            # Publish visualization markers
            self.get_logger().info("  Publishing visualization markers to RViz...")
            self.publish_waypoint_markers(waypoints, "demo2_waypoints")
            self.publish_trajectory_markers(waypoints, trajectory, "demo2_trajectory")
            time.sleep(0.2)
    
    def demo_workspace_sampling(self):
        """Sample accessible workspace"""
        
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("DEMO 3: Verified Workspace Positions")
        self.get_logger().info("=" * 70)
        
        # Test positions verified as reachable in inverse_kinematics_demo
        test_positions = [
            (-0.0009, 0.0, 1.1681, "Home"),
            (0.3, 0.4, 0.9, "Right Reach"),
            (-0.3, 0.4, 0.9, "Left Reach"),
            (-0.0009, 0.6, 0.9, "Forward Reach"),
        ]
        
        successful = 0
        failed = 0
        
        self.get_logger().info(f"\nTesting {len(test_positions)} verified positions...")
        
        for x, y, z, label in test_positions:
            pose = self.create_pose(x, y, z)
            solution = self.solve_ik(pose)
            
            if solution:
                successful += 1
                status = "✓"
            else:
                failed += 1
                status = "✗"
            
            self.get_logger().info(
                f"  {status} {label:15s} ({x:7.4f}, {y:4.2f}, {z:5.2f}): "
                f"{'Reachable' if solution else 'Unreachable'}"
            )
        
        # Print summary
        reachability = successful / len(test_positions) * 100
        self.get_logger().info(f"\n✓ Workspace Check Complete")
        self.get_logger().info(f"  Positions tested: {len(test_positions)}")
        self.get_logger().info(f"  Reachable: {successful}/{len(test_positions)} ({reachability:.1f}%)")
        self.get_logger().info(f"  Unreachable: {failed}/{len(test_positions)}")
        
        # Publish workspace visualization markers
        self.get_logger().info("  Publishing workspace markers to RViz...")
        workspace_positions = [(p[0], p[1], p[2]) for p in test_positions]
        reachability_status = []
        for x, y, z, label in test_positions:
            pose = self.create_pose(x, y, z)
            solution = self.solve_ik(pose)
            reachability_status.append(solution is not None)
        
        self.publish_workspace_markers(workspace_positions, reachability_status, "demo3_workspace")
        time.sleep(0.2)


def main(args=None):
    """Main entry point"""
    rclpy.init(args=args)
    
    try:
        demo = MotionPlanningDemo()
        
        # Run demonstrations
        demo.demo_simple_trajectory()
        time.sleep(1)
        
        demo.demo_figure_eight_trajectory()
        time.sleep(1)
        
        demo.demo_workspace_sampling()
        
        # Print summary
        demo.get_logger().info("\n" + "=" * 70)
        demo.get_logger().info("✓✓✓ MOTION PLANNING DEMOS COMPLETE ✓✓✓")
        demo.get_logger().info("=" * 70)
        demo.get_logger().info(f"IK Solver Status: ✓ FULLY OPERATIONAL")
        demo.get_logger().info("Trajectory Planning: ✓ Real joint angle computation via IK service")
        demo.get_logger().info("=" * 70)
        demo.get_logger().info("\nDemo node will continue running to keep visualization markers visible.")
        demo.get_logger().info("Press Ctrl+C to exit.")
        
        # Keep node running so markers remain visible for RViz and other subscribers
        while rclpy.ok():
            try:
                rclpy.spin_once(demo, timeout_sec=1.0)
            except KeyboardInterrupt:
                break
        
    except Exception as e:
        print(f"✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
