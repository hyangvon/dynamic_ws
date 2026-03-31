#!/usr/bin/env python3
"""
Joint State Publisher for W10 Robot
Publishes default joint states to enable TF tree generation
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import time

class JointStatePublisher(Node):
    def __init__(self):
        super().__init__('joint_state_publisher')
        
        # Publisher for joint states
        self.pub = self.create_publisher(JointState, '/joint_states', 10)
        
        # Create timer to publish at 10 Hz
        self.timer = self.create_timer(0.1, self.publish_joint_states)
        
        # Joint names for W10 (7-DOF)
        self.joint_names = ['joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
        
        # Default positions
        self.joint_positions = [0.0] * len(self.joint_names)
        self.joint_velocities = [0.0] * len(self.joint_names)
        self.joint_efforts = [0.0] * len(self.joint_names)
        
        self.get_logger().info("✓ Joint State Publisher initialized")
        self.get_logger().info(f"  Publishing {len(self.joint_names)} joints: {', '.join(self.joint_names)}")
    
    def publish_joint_states(self):
        """Publish joint states"""
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = self.joint_positions
        msg.velocity = self.joint_velocities
        msg.effort = self.joint_efforts
        
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = JointStatePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
