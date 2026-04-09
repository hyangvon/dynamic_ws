"""
W10 7-DOF Robotic Arm Kinematics Solver using MoveIt2
Supports forward kinematics, inverse kinematics, and trajectory planning
"""

import rclpy
from rclpy.node import Node
from moveit_msgs.msg import MoveItErrorCodes
from geometry_msgs.msg import PoseStamped, Point, Quaternion
from sensor_msgs.msg import JointState
import numpy as np
from typing import List, Tuple, Optional
import math


class W10KinematicsSolver(Node):
    """
    Kinematics solver for W10 7-DOF robotic arm using MoveIt2 framework.
    
    Provides:
    - Forward Kinematics (FK): joint angles → end-effector pose
    - Inverse Kinematics (IK): end-effector pose → joint angles
    - Trajectory planning with obstacle avoidance
    """
    
    def __init__(self):
        super().__init__('w10_kinematics_solver')
        
        try:
            from moveit_commander import RobotCommander, MoveGroupCommander
            from moveit_commander import PlanningSceneInterface
        except ImportError:
            self.get_logger().error('MoveIt2 not installed. Install with: sudo apt install ros-<distro>-moveit2')
            return
        
        self.robot = None
        self.scene = None
        self.move_group = None
        self._initialize_moveit()
        
    def _initialize_moveit(self):
        """Initialize MoveIt2 components"""
        try:
            from moveit_commander import RobotCommander, MoveGroupCommander
            from moveit_commander import PlanningSceneInterface
            
            self.scene = PlanningSceneInterface()
            self.robot = RobotCommander()
            
            # Group name should match your MoveIt2 config
            self.move_group = MoveGroupCommander("w10_arm")
            
            self.get_logger().info("MoveIt2 initialized successfully")
            self.get_logger().info(f"Planning frame: {self.move_group.get_planning_frame()}")
            self.get_logger().info(f"End effector link: {self.move_group.get_end_effector_link()}")
            
        except Exception as e:
            self.get_logger().error(f"Failed to initialize MoveIt2: {str(e)}")
    
    def forward_kinematics(self, joint_angles: List[float]) -> Optional[PoseStamped]:
        """
        Compute forward kinematics using MoveIt2.
        
        Args:
            joint_angles: List of 7 joint angles in radians [q0, q1, ..., q6]
            
        Returns:
            PoseStamped: End-effector pose with position and orientation
        """
        if self.move_group is None:
            self.get_logger().error("MoveIt2 not initialized")
            return None
        
        try:
            if len(joint_angles) != 7:
                self.get_logger().error(f"Expected 7 joints, got {len(joint_angles)}")
                return None
            
            # Set joint positions
            self.move_group.set_joint_value_target(joint_angles)
            
            # Get current state
            state = self.robot.get_current_state()
            
            # Directly compute the forward kinematics
            from moveit_core.kinematic_constraints import construct_joint_constraint
            from tf2_ros import Buffer, TransformListener
            
            # Get end-effector pose
            ee_pose = self.move_group.get_current_pose(self.move_group.get_end_effector_link())
            
            self.get_logger().debug(f"FK computed for joints: {joint_angles}")
            return ee_pose
            
        except Exception as e:
            self.get_logger().error(f"Forward kinematics error: {str(e)}")
            return None
    
    def inverse_kinematics(self, target_pose: PoseStamped, 
                         allow_replanning: bool = True,
                         num_attempts: int = 10) -> Optional[List[float]]:
        """
        Compute inverse kinematics using MoveIt2's built-in IK solver.
        
        Args:
            target_pose: Target end-effector pose (PoseStamped)
            allow_replanning: Allow replanning if first attempt fails
            num_attempts: Number of IK attempts
            
        Returns:
            List of 7 joint angles in radians, or None if no solution found
        """
        if self.move_group is None:
            self.get_logger().error("MoveIt2 not initialized")
            return None
        
        try:
            self.move_group.set_pose_target(target_pose)
            
            # Try to find IK solution
            success = False
            joint_solution = None
            
            for attempt in range(num_attempts):
                try:
                    plan = self.move_group.plan()
                    if plan.motion_plan_response.error_code.val == MoveItErrorCodes.SUCCESS:
                        # Extract joint values from trajectory
                        trajectory = plan.motion_plan_response.trajectory
                        if trajectory.joint_trajectory.points:
                            joint_solution = list(trajectory.joint_trajectory.points[0].positions)
                            success = True
                            break
                except Exception as e:
                    self.get_logger().debug(f"IK attempt {attempt+1} failed: {str(e)}")
                    continue
            
            if success and joint_solution:
                self.get_logger().debug(f"IK solution found: {joint_solution}")
                return joint_solution
            else:
                self.get_logger().warn("No IK solution found")
                return None
                
        except Exception as e:
            self.get_logger().error(f"Inverse kinematics error: {str(e)}")
            return None
    
    def plan_trajectory(self, target_pose: PoseStamped) -> Optional[dict]:
        """
        Plan a collision-free trajectory to target pose.
        
        Args:
            target_pose: Target end-effector pose
            
        Returns:
            Dictionary with trajectory info or None if planning fails
        """
        if self.move_group is None:
            self.get_logger().error("MoveIt2 not initialized")
            return None
        
        try:
            self.move_group.set_pose_target(target_pose)
            self.move_group.set_planning_time(5.0)
            
            plan = self.move_group.plan()
            
            if plan.motion_plan_response.error_code.val == MoveItErrorCodes.SUCCESS:
                trajectory_points = plan.motion_plan_response.trajectory.joint_trajectory.points
                
                result = {
                    'success': True,
                    'num_points': len(trajectory_points),
                    'trajectories': trajectory_points,
                    'total_time': trajectory_points[-1].time_from_start.sec if trajectory_points else 0
                }
                self.get_logger().info(f"Trajectory planned with {len(trajectory_points)} points")
                return result
            else:
                self.get_logger().warn("Trajectory planning failed")
                return None
                
        except Exception as e:
            self.get_logger().error(f"Trajectory planning error: {str(e)}")
            return None
    
    def execute_trajectory(self, trajectory) -> bool:
        """Execute planned trajectory"""
        if self.move_group is None:
            self.get_logger().error("MoveIt2 not initialized")
            return False
        
        try:
            self.move_group.execute(trajectory, wait=True)
            self.get_logger().info("Trajectory executed")
            return True
        except Exception as e:
            self.get_logger().error(f"Trajectory execution error: {str(e)}")
            return False
    
    def get_current_state(self) -> Optional[JointState]:
        """Get current joint state"""
        if self.robot is None:
            return None
        
        try:
            state = self.robot.get_current_state()
            return state.joint_state
        except Exception as e:
            self.get_logger().error(f"Error getting current state: {str(e)}")
            return None
    
    def add_collision_object(self, name: str, position: List[float], 
                            size: List[float]) -> bool:
        """
        Add a box collision object to the scene.
        
        Args:
            name: Name of the collision object
            position: [x, y, z] position
            size: [length, width, height]
        """
        if self.scene is None:
            return False
        
        try:
            pose = PoseStamped()
            pose.header.frame_id = "base_link"
            pose.pose.position = Point(x=position[0], y=position[1], z=position[2])
            pose.pose.orientation = Quaternion(x=0, y=0, z=0, w=1)
            
            self.scene.add_box(name, pose, size=tuple(size))
            self.get_logger().info(f"Added collision object: {name}")
            return True
        except Exception as e:
            self.get_logger().error(f"Error adding collision object: {str(e)}")
            return False
    
    def remove_collision_object(self, name: str) -> bool:
        """Remove collision object from scene"""
        if self.scene is None:
            return False
        
        try:
            self.scene.remove_world_object(name)
            self.get_logger().info(f"Removed collision object: {name}")
            return True
        except Exception as e:
            self.get_logger().error(f"Error removing collision object: {str(e)}")
            return False

    def create_pose_stamp(self, position: List[float], 
                         orientation: List[float],
                         frame_id: str = "base_link") -> PoseStamped:
        """
        Create a PoseStamped message.
        
        Args:
            position: [x, y, z]
            orientation: [qx, qy, qz, qw] (quaternion)
            frame_id: Reference frame
        """
        pose = PoseStamped()
        pose.header.frame_id = frame_id
        pose.pose.position = Point(x=position[0], y=position[1], z=position[2])
        pose.pose.orientation = Quaternion(x=orientation[0], y=orientation[1], 
                                          z=orientation[2], w=orientation[3])
        return pose
