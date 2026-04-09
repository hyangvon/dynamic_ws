#!/usr/bin/env python3
"""
Interactive Kinematics Tool for W10 7-DOF Robotic Arm

A command-line tool for interactive exploration of kinematics
"""

import rclpy
from rclpy.node import Node
import math
import sys

try:
    from moveit_commander import RobotCommander, MoveGroupCommander
    from moveit_msgs.msg import MoveItErrorCodes
except ImportError:
    print("ERROR: moveit2 not installed!")
    sys.exit(1)

from geometry_msgs.msg import PoseStamped, Point, Quaternion


class InteractiveKinematicsTool(Node):
    """Interactive kinematics exploration tool"""
    
    def __init__(self):
        super().__init__('interactive_kinematics')
        
        try:
            self.robot = RobotCommander()
            self.move_group = MoveGroupCommander("w10_arm")
            self.get_logger().info("MoveIt2 initialized")
            self.running = True
        except Exception as e:
            self.get_logger().error(f"Failed to initialize: {e}")
            self.running = False
    
    def create_pose(self, x, y, z, qx=0, qy=0, qz=0, qw=1):
        """Create a PoseStamped message"""
        pose = PoseStamped()
        pose.header.frame_id = "base_link"
        pose.pose.position = Point(x=x, y=y, z=z)
        pose.pose.orientation = Quaternion(x=qx, y=qy, z=qz, w=qw)
        return pose
    
    def display_menu(self):
        """Display main menu"""
        print("\n" + "=" * 60)
        print("W10 Interactive Kinematics Tool")
        print("=" * 60)
        print("1. Forward Kinematics (FK)")
        print("2. Inverse Kinematics (IK)")
        print("3. List Joint Ranges")
        print("4. Move to Joint Configuration")
        print("5. Move to Cartesian Position")
        print("6. Show Current State")
        print("7. Exit")
        print("=" * 60)
    
    def forward_kinematics_interactive(self):
        """Interactive FK computation"""
        print("\n--- Forward Kinematics ---")
        print("Enter 7 joint angles (in radians, space-separated)")
        print("Example: 0 0.5 0 -0.5 0 0.5 0")
        try:
            input_str = input("> ")
            joints = [float(x) for x in input_str.split()]
            
            if len(joints) != 7:
                print(f"ERROR: Expected 7 joints, got {len(joints)}")
                return
            
            self.move_group.set_joint_value_target(joints)
            pose = self.move_group.get_current_pose(
                self.move_group.get_end_effector_link()
            )
            
            pos = pose.pose.position
            orn = pose.pose.orientation
            
            print(f"\nEnd-Effector Pose:")
            print(f"Position (m): X={pos.x:.4f}, Y={pos.y:.4f}, Z={pos.z:.4f}")
            print(f"Orientation (quaternion): X={orn.x:.4f}, Y={orn.y:.4f}, Z={orn.z:.4f}, W={orn.w:.4f}")
            
            # Compute RPY
            roll, pitch, yaw = self._quaternion_to_rpy(orn)
            print(f"Orientation (RPY rad): R={roll:.4f}, P={pitch:.4f}, Y={yaw:.4f}")
            print(f"Orientation (RPY deg): R={math.degrees(roll):.2f}°, P={math.degrees(pitch):.2f}°, Y={math.degrees(yaw):.2f}°")
            
        except ValueError:
            print("ERROR: Invalid input. Please enter 7 numbers separated by spaces.")
        except Exception as e:
            print(f"ERROR: {e}")
    
    def inverse_kinematics_interactive(self):
        """Interactive IK computation"""
        print("\n--- Inverse Kinematics ---")
        print("Enter target position (x y z in meters)")
        print("Example: 0.0 0.4 0.5")
        try:
            input_str = input("> ")
            x, y, z = [float(val) for val in input_str.split()]
            
            target_pose = self.create_pose(x, y, z)
            self.move_group.set_pose_target(target_pose)
            
            plan = self.move_group.plan()
            
            if plan.motion_plan_response.error_code.val == MoveItErrorCodes.SUCCESS:
                trajectory = plan.motion_plan_response.trajectory
                if trajectory.joint_trajectory.points:
                    joints = trajectory.joint_trajectory.points[0].positions
                    print(f"\nIK Solution Found!")
                    print(f"Joint Angles (radians):")
                    for i, angle in enumerate(joints):
                        print(f"  q{i+1} = {angle:.4f} rad ({math.degrees(angle):.2f}°)")
                else:
                    print("ERROR: No trajectory points")
            else:
                print(f"ERROR: IK Failed - Error Code: {plan.motion_plan_response.error_code.val}")
                
        except ValueError:
            print("ERROR: Invalid input. Please enter 3 numbers.")
        except Exception as e:
            print(f"ERROR: {e}")
    
    def list_joint_ranges(self):
        """List joint limits"""
        print("\n--- Joint Ranges ---")
        print(f"Planning frame: {self.move_group.get_planning_frame()}")
        print(f"End-effector link: {self.move_group.get_end_effector_link()}")
        
        print("\nJoint Limits:")
        try:
            # Get from robot model
            robot_model = self.robot.get_robot_model()
            for joint in robot_model.joints:
                if 'joint' in joint.name and 'fixed' not in joint.type.lower():
                    print(f"\n{joint.name}:")
                    if hasattr(joint, 'safety_controller'):
                        print(f"  Type: {joint.type}")
                        if hasattr(joint, 'limits'):
                            print(f"  Lower: {joint.limits.lower:.4f} rad")
                            print(f"  Upper: {joint.limits.upper:.4f} rad")
        except Exception as e:
            print(f"Could not retrieve joint limits: {e}")
    
    def move_to_configuration(self):
        """Move to specific joint configuration"""
        print("\n--- Move to Configuration ---")
        print("Enter 7 joint angles (in radians)")
        try:
            input_str = input("> ")
            joints = [float(x) for x in input_str.split()]
            
            if len(joints) != 7:
                print(f"ERROR: Expected 7 joints, got {len(joints)}")
                return
            
            self.move_group.set_joint_value_target(joints)
            plan = self.move_group.plan()
            
            if plan.motion_plan_response.error_code.val == MoveItErrorCodes.SUCCESS:
                print("Planning successful!")
                print(f"Trajectory points: {len(plan.motion_plan_response.trajectory.joint_trajectory.points)}")
                
                confirm = input("Execute motion? (y/n): ")
                if confirm.lower() == 'y':
                    self.move_group.execute(plan, wait=True)
                    print("Motion executed!")
            else:
                print(f"Planning failed - Error Code: {plan.motion_plan_response.error_code.val}")
                
        except ValueError:
            print("ERROR: Invalid input.")
        except Exception as e:
            print(f"ERROR: {e}")
    
    def move_to_cartesian(self):
        """Move to specific Cartesian position"""
        print("\n--- Move to Cartesian Position ---")
        print("Enter target position (x y z in meters)")
        try:
            input_str = input("> ")
            x, y, z = [float(val) for val in input_str.split()]
            
            target_pose = self.create_pose(x, y, z)
            self.move_group.set_pose_target(target_pose)
            plan = self.move_group.plan()
            
            if plan.motion_plan_response.error_code.val == MoveItErrorCodes.SUCCESS:
                print("Planning successful!")
                print(f"Trajectory points: {len(plan.motion_plan_response.trajectory.joint_trajectory.points)}")
                
                confirm = input("Execute motion? (y/n): ")
                if confirm.lower() == 'y':
                    self.move_group.execute(plan, wait=True)
                    print("Motion executed!")
            else:
                print(f"Planning failed - Error Code: {plan.motion_plan_response.error_code.val}")
                
        except ValueError:
            print("ERROR: Invalid input.")
        except Exception as e:
            print(f"ERROR: {e}")
    
    def show_current_state(self):
        """Display current robot state"""
        print("\n--- Current State ---")
        try:
            state = self.robot.get_current_state()
            
            print("Current Joint Positions (radians):")
            if state.joint_state.position:
                for i, (name, pos) in enumerate(zip(state.joint_state.name, state.joint_state.position)):
                    if 'joint' in name:
                        print(f"  {name}: {pos:.4f} rad ({math.degrees(pos):.2f}°)")
            
            # Show current pose
            current_pose = self.move_group.get_current_pose(
                self.move_group.get_end_effector_link()
            )
            
            pos = current_pose.pose.position
            print(f"\nEnd-Effector Position (m):")
            print(f"  X: {pos.x:.4f}")
            print(f"  Y: {pos.y:.4f}")
            print(f"  Z: {pos.z:.4f}")
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    @staticmethod
    def _quaternion_to_rpy(quaternion):
        """Convert quaternion to roll, pitch, yaw"""
        x = quaternion.x
        y = quaternion.y
        z = quaternion.z
        w = quaternion.w
        
        roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
        sin_pitch = 2 * (w * y - z * x)
        sin_pitch = max(-1, min(1, sin_pitch))
        pitch = math.asin(sin_pitch)
        yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        
        return roll, pitch, yaw
    
    def run(self):
        """Main interactive loop"""
        if not self.running:
            print("Failed to initialize. Exiting.")
            return
        
        while self.running:
            self.display_menu()
            choice = input("Select option (1-7): ").strip()
            
            if choice == '1':
                self.forward_kinematics_interactive()
            elif choice == '2':
                self.inverse_kinematics_interactive()
            elif choice == '3':
                self.list_joint_ranges()
            elif choice == '4':
                self.move_to_configuration()
            elif choice == '5':
                self.move_to_cartesian()
            elif choice == '6':
                self.show_current_state()
            elif choice == '7':
                print("Exiting...")
                self.running = False
            else:
                print("Invalid option. Please try again.")


def main(args=None):
    rclpy.init(args=args)
    
    try:
        tool = InteractiveKinematicsTool()
        tool.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
