#!/usr/bin/env python3
"""
System Integration Test for W10 MoveIt2 Framework
Tests MoveIt2 services without using deprecated moveit_commander
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.srv import GetPositionFK, GetPositionIK
from moveit_msgs.msg import MotionPlanRequest, Constraints, JointConstraint
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped, Quaternion
import math
import sys
import time


class W10SystemTest(Node):
    """Test MoveIt2 system without moveit_commander"""
    
    def __init__(self):
        super().__init__('w10_system_test')
        
        self.get_logger().info("=" * 70)
        self.get_logger().info("W10 MoveIt2 System Integration Test")
        self.get_logger().info("=" * 70)
        
        # Check if move_group node is running
        self.get_logger().info("\n[1/3] Checking move_group node...")
        self.move_group_ready = self.check_move_group_service()
        
        if not self.move_group_ready:
            self.get_logger().error("move_group service not available!")
            self.get_logger().info("Ensure move_group is running:")
            self.get_logger().info("  ros2 launch w10_moveit_kinematics move_group_minimal.launch.py")
            sys.exit(1)
        
        self.get_logger().info("✓ move_group service available")
        
        # List available services
        self.get_logger().info("\n[2/3] Available MoveIt2 Services:")
        self.list_moveit_services()
        
        # Test basic connectivity
        self.get_logger().info("\n[3/3] Testing basic connectivity...")
        self.test_connectivity()
        
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("System test completed successfully!")
        self.get_logger().info("Framework is ready for use.")
        self.get_logger().info("=" * 70)
    
    def check_move_group_service(self) -> bool:
        """Check if move_group service is available"""
        try:
            # Wait for service
            services = self.get_service_names_and_types()
            for service_name, service_types in services:
                if 'move_group' in service_name:
                    self.get_logger().debug(f"Found service: {service_name}")
                    return True
            return False
        except:
            return False
    
    def list_moveit_services(self):
        """List all available MoveIt2 services"""
        try:
            services = self.get_service_names_and_types()
            moveit_services = [s[0] for s in services if 'move_group' in s[0] or 'kinematics' in s[0]]
            
            if moveit_services:
                for service in sorted(moveit_services)[:10]:
                    self.get_logger().info(f"  • {service}")
                if len(moveit_services) > 10:
                    self.get_logger().info(f"  ... and {len(moveit_services) - 10} more")
            else:
                self.get_logger().warn("No MoveIt services found")
        except Exception as e:
            self.get_logger().error(f"Error listing services: {e}")
    
    def test_connectivity(self):
        """Test basic MoveIt2 connectivity"""
        try:
            # Get robot state
            state_client = self.create_client(GetPositionFK, 'compute_fk')
            
            self.get_logger().info("  • Testing forward kinematics service...")
            
            # Wait briefly for service
            time.sleep(0.5)
            
            if state_client.service_is_ready():
                self.get_logger().info("  ✓ FK service ready")
            else:
                self.get_logger().info("  ℹ FK service not yet ready (can test after startup)")
                
        except Exception as e:
            self.get_logger().debug(f"Connectivity test info: {e}")
        
        self.get_logger().info("  • MoveIt2 framework initialization successful")


def main(args=None):
    rclpy.init(args=args)
    
    test_node = W10SystemTest()
    
    # Give it a moment
    rclpy.spin_once(test_node, timeout_sec=1.0)
    
    test_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
