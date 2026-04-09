#!/usr/bin/env python3
"""
w10机械臂关节控制脚本
发送JointState消息来控制机械臂的关节角度
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from builtin_interfaces.msg import Time
import math
import argparse
import time

class W10JointController(Node):
    def __init__(self):
        super().__init__('w10_joint_controller')
        self.publisher = self.create_publisher(JointState, 'joint_states', 10)
        
        self.joint_names = ['joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
        
    def publish_joint_state(self, positions):
        """
        发布关节状态
        Args:
            positions: 列表，每个元素对应一个关节的角度（弧度）
        """
        if len(positions) != len(self.joint_names):
            self.get_logger().error(
                f'关节数不匹配！期望{len(self.joint_names)}个，得到{len(positions)}个'
            )
            return False
        
        # 创建JointState消息
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.name = self.joint_names
        msg.position = positions
        msg.velocity = [0.0] * len(self.joint_names)
        msg.effort = [0.0] * len(self.joint_names)
        
        self.publisher.publish(msg)
        self.get_logger().info(f'发布关节状态: {[f"{x:.3f}" for x in positions]}')
        return True
    
    def move_to_home(self):
        """移动到零位置"""
        self.get_logger().info('移动到HOME位置 (所有关节=0)')
        return self.publish_joint_state([0.0] * len(self.joint_names))
    
    def move_to_config(self, name):
        """移动到预定义配置"""
        configs = {
            'demo1': [0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.0],
            'demo2': [0.2, -0.1, 0.5, 0.2, 0.0, 0.0, 0.0],
            'demo3': [-0.3, 0.4, -0.2, 0.1, 0.2, 0.0, 0.0],
            'reach_up': [0.0, -1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        }
        
        if name not in configs:
            self.get_logger().error(f'未知配置: {name}')
            self.get_logger().info(f'可用配置: {list(configs.keys())}')
            return False
        
        config = configs[name]
        self.get_logger().info(f'移动到配置: {name}')
        return self.publish_joint_state(config)
    
    def sweep_joints(self, amplitude=0.5, period=4.0, duration=10.0):
        """
        扫动所有关节
        Args:
            amplitude: 振幅（弧度）
            period: 周期（秒）
            duration: 总时间（秒）
        """
        self.get_logger().info(f'开始扫动关节 (幅度={amplitude:.2f}rad, 周期={period:.2f}s, 时长={duration:.2f}s)')
        
        start_time = time.time()
        while (time.time() - start_time) < duration:
            t = time.time() - start_time
            # 使用正弦波扫动所有关节
            phase = (2 * math.pi * t) / period
            positions = [amplitude * math.sin(phase + i * 0.5) for i in range(len(self.joint_names))]
            self.publish_joint_state(positions)
            time.sleep(0.1)
        
        # 回到HOME位置
        self.move_to_home()
        self.get_logger().info('扫动完成，回到HOME位置')

def main():
    rclpy.init()
    
    controller = W10JointController()
    
    parser = argparse.ArgumentParser(description='w10机械臂关节控制')
    parser.add_argument(
        'command',
        choices=['home', 'config', 'sweep'],
        help='命令: home(回零), config(预定义配置), sweep(扫动)'
    )
    parser.add_argument(
        '--config',
        choices=['demo1', 'demo2', 'demo3', 'reach_up'],
        default='demo1',
        help='预定义配置名称'
    )
    parser.add_argument(
        '--amplitude',
        type=float,
        default=0.5,
        help='扫动幅度（弧度）'
    )
    parser.add_argument(
        '--period',
        type=float,
        default=4.0,
        help='扫动周期（秒）'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=10.0,
        help='扫动持续时间（秒）'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'home':
            controller.move_to_home()
        
        elif args.command == 'config':
            controller.move_to_config(args.config)
        
        elif args.command == 'sweep':
            controller.sweep_joints(
                amplitude=args.amplitude,
                period=args.period,
                duration=args.duration
            )
        
        rclpy.spin_once(controller, timeout_sec=1.0)
    
    except KeyboardInterrupt:
        controller.get_logger().info('中断')
    
    finally:
        controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
