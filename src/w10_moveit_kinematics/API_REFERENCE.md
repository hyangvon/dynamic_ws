# API 参考文档

如何在你的Python代码中调用IK和FK功能。

## 🔗 导入与初始化

```python
import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPositionIK, GetPositionFK
from moveit_msgs.msg import RobotState
from geometry_msgs.msg import PoseStamped, Point, Quaternion
from sensor_msgs.msg import JointState

class MyKinematicsApp(Node):
    def __init__(self):
        super().__init__('my_app')
        
        # 创建IK和FK服务客户端
        self.ik_client = self.create_client(GetPositionIK, '/compute_ik')
        self.fk_client = self.create_client(GetPositionFK, '/compute_fk')
        
        # 等待服务就绪
        while not self.ik_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('等待 /compute_ik 服务...')
        self.get_logger().info('✓ 服务已就绪')
```

## 🎯 使用IK（逆运动学）

### 基础用法

```python
def solve_ik(self, target_pose: tuple) -> list|None:
    """
    求解逆运动学
    
    Args:
        target_pose: (x, y, z, qx, qy, qz, qw) 目标姿态
        
    Returns:
        光带角列表 [j2, j3, j4, j5, j6, j7, j8] 或 None (失败)
    """
    x, y, z, qx, qy, qz, qw = target_pose
    
    # 1. 创建目标姿态消息
    pose = PoseStamped()
    pose.header.frame_id = "base_link"
    pose.pose.position = Point(x=float(x), y=float(y), z=float(z))
    pose.pose.orientation = Quaternion(
        x=float(qx), y=float(qy), z=float(qz), w=float(qw)
    )
    
    # 2. 创建IK请求
    request = GetPositionIK.Request()
    request.ik_request.group_name = 'w10_arm'
    request.ik_request.pose_stamped = pose
    request.ik_request.ik_link_name = 'Link8'
    request.ik_request.timeout.sec = 5
    
    # 3. 设置初始关节状态（seed state）
    robot_state = RobotState()
    robot_state.joint_state.name = [
        'joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8'
    ]
    robot_state.joint_state.position = [0.0] * 7  # Home配置
    request.ik_request.robot_state = robot_state
    
    # 4. 异步调用服务
    try:
        future = self.ik_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=6.0)
        
        if future.result() is None:
            self.get_logger().error("IK服务无响应")
            return None
            
        response = future.result()
        
        # 5. 检查结果
        if response.error_code.val == 1:  # SUCCESS
            return list(response.solution.joint_state.position)
        else:
            self.get_logger().warn(f"IK失败: error_code={response.error_code.val}")
            return None
            
    except Exception as e:
        self.get_logger().error(f"IK异常: {e}")
        return None
```

### 高级用法 - 带初值

```python
def solve_ik_with_seed(self, target_pose: tuple, seed_config: list) -> list|None:
    """
    用特定初值求IK (会更快收敛)
    
    Args:
        target_pose: 目标姿态
        seed_config: 初始关节配置 [j2, j3, ..., j8]
    """
    # ... (前面代码同上) ...
    
    # 只需修改这部分：
    robot_state.joint_state.position = seed_config
    
    # ... (rest of code) ...
```

### 应用示例 - 多目标轨迹

```python
def plan_trajectory(self, waypoints: list[tuple]) -> list[list]:
    """
    规划通过多个路径点的轨迹
    
    Args:
        waypoints: [(x1,y1,z1,qx,qy,qz,qw), (x2,y2,z2,...), ...]
        
    Returns:
        [[j2,j3,...,j8], [j2,j3,...,j8], ...] 关节轨迹
    """
    trajectory = []
    
    for waypoint in waypoints:
        joint_config = self.solve_ik(waypoint)
        if joint_config is None:
            self.get_logger().error(f"路径点 {waypoint} 无解!")
            return None
        trajectory.append(joint_config)
    
    return trajectory

# 使用
waypoints = [
    (0.0, 0.0, 1.17, 0, 0, -0.707, 0.707),    # 点1
    (0.2, 0.1, 1.0, 0, 0, -0.707, 0.707),     # 点2
    (0.3, 0.2, 0.9, 0, 0, -0.707, 0.707),     # 点3
]
trajectory = my_app.plan_trajectory(waypoints)
```

## 📐 使用FK（正向运动学）

### 基础用法

```python
def compute_fk(self, joint_angles: list) -> tuple|None:
    """
    计算正向运动学
    
    Args:
        joint_angles: [j2, j3, j4, j5, j6, j7, j8] 关节角
        
    Returns:
        (x, y, z, qx, qy, qz, qw) 末端位置/姿态 或 None (失败)
    """
    
    # 1. 创建FK请求
    request = GetPositionFK.Request()
    request.header.frame_id = 'base_link'
    request.fk_link_names = ['Link8']  # 查询Link8的位置
    
    # 2. 设置关节状态
    robot_state = RobotState()
    robot_state.joint_state.name = [
        'joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8'
    ]
    robot_state.joint_state.position = joint_angles
    request.robot_state = robot_state
    
    # 3. 调用服务
    try:
        future = self.fk_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
        
        response = future.result()
        
        if response.error_code.val == 1:  # SUCCESS
            pose = response.pose_stamped[0]
            return (
                pose.pose.position.x,
                pose.pose.position.y,
                pose.pose.position.z,
                pose.pose.orientation.x,
                pose.pose.orientation.y,
                pose.pose.orientation.z,
                pose.pose.orientation.w,
            )
        else:
            self.get_logger().warn("FK失败")
            return None
            
    except Exception as e:
        self.get_logger().error(f"FK异常: {e}")
        return None
```

### 应用示例 - FK验证

```python
def verify_ik_solution(self, target_pose: tuple, ik_solution: list) -> bool:
    """
    验证IK解是否正确 (FK逆验证)
    """
    computed_pose = self.compute_fk(ik_solution)
    
    if computed_pose is None:
        return False
    
    # 检查位置误差 (允许5mm误差)
    pos_error = sum((computed_pose[i] - target_pose[i])**2 for i in range(3)) ** 0.5
    
    if pos_error > 0.005:  # >5mm视为失败
        self.get_logger().warn(f"位置误差过大: {pos_error:.4f}m")
        return False
    
    self.get_logger().info("✓ IK解验证通过")
    return True
```

## 🛠️ 辅助函数

### 创建姿态消息

```python
def create_pose(self, x, y, z, qx=0, qy=0, qz=0, qw=1) -> PoseStamped:
    """快速创建PoseStamped消息"""
    pose = PoseStamped()
    pose.header.frame_id = "base_link"
    pose.pose.position = Point(x=float(x), y=float(y), z=float(z))
    pose.pose.orientation = Quaternion(
        x=float(qx), y=float(qy), z=float(qz), w=float(qw)
    )
    return pose
```

### 四元数与欧拉角转换

```python
import math
from scipy.spatial.transform import Rotation

def euler_to_quaternion(roll, pitch, yaw):
    """欧拉角 → 四元数"""
    r = Rotation.from_euler('xyz', [roll, pitch, yaw])
    q = r.as_quat()  # [qx, qy, qz, qw]
    return q

def quaternion_to_euler(qx, qy, qz, qw):
    """四元数 → 欧拉角"""
    r = Rotation.from_quat([qx, qy, qz, qw])
    euler = r.as_euler('xyz')  # [roll, pitch, yaw]
    return euler

# 使用
qx, qy, qz, qw = euler_to_quaternion(0, 0, -math.pi/4)
pose = self.create_pose(0.3, 0.2, 0.9, qx, qy, qz, qw)
```

### 关节限制检查

```python
def is_within_limits(self, joint_angles: list) -> bool:
    """检查关节角是否在限制范围内"""
    limits = {
        'joint2': (-3.14, 3.14),
        'joint3': (-3.14, 3.14),
        'joint4': (-3.14, 3.14),
        'joint5': (-3.14, 3.14),
        'joint6': (-3.14, 3.14),
        'joint7': (-3.14, 3.14),
        'joint8': (-3.14, 3.14),
    }
    
    for i, (joint_name, (min_val, max_val)) in enumerate(limits.items()):
        if not (min_val <= joint_angles[i] <= max_val):
            self.get_logger().warn(f"{joint_name}超出限制: {joint_angles[i]}")
            return False
    
    return True
```

## 📊 完整示例程序

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import RobotState
from geometry_msgs.msg import PoseStamped, Point, Quaternion
import math

class DemoApp(Node):
    def __init__(self):
        super().__init__('demo_app')
        self.ik_client = self.create_client(GetPositionIK, '/compute_ik')
        while not self.ik_client.wait_for_service(timeout_sec=1.0):
            pass
        self.get_logger().info("✓ 服务就绪")
    
    def create_pose(self, x, y, z, qz=-0.707, qw=0.707):
        pose = PoseStamped()
        pose.header.frame_id = "base_link"
        pose.pose.position = Point(x=x, y=y, z=z)
        pose.pose.orientation = Quaternion(x=0.0, y=0.0, z=qz, w=qw)
        return pose
    
    def solve_ik(self, pose: PoseStamped):
        request = GetPositionIK.Request()
        request.ik_request.group_name = 'w10_arm'
        request.ik_request.pose_stamped = pose
        request.ik_request.ik_link_name = 'Link8'
        request.ik_request.timeout.sec = 5
        
        robot_state = RobotState()
        robot_state.joint_state.name = ['joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
        robot_state.joint_state.position = [0.0] * 7
        request.ik_request.robot_state = robot_state
        
        future = self.ik_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=6.0)
        
        response = future.result()
        if response.error_code.val == 1:
            return list(response.solution.joint_state.position)
        return None
    
    def run(self):
        poses = [
            (0.0, 0.0, 1.17),
            (0.2, 0.1, 1.0),
            (0.3, 0.2, 0.9),
        ]
        
        for x, y, z in poses:
            pose = self.create_pose(x, y, z)
            joints = self.solve_ik(pose)
            if joints:
                print(f"✓ ({x:.1f}, {y:.1f}, {z:.1f}) → {[f'{j:.2f}' for j in joints]}")
            else:
                print(f"✗ ({x:.1f}, {y:.1f}, {z:.1f}) 无解")

def main():
    rclpy.init()
    app = DemoApp()
    app.run()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## 📌 常用参数速查

| 参数 | 值 | 说明 |
|------|-----|------|
| `group_name` | `'w10_arm'` | 运动组名 |
| `ik_link_name` | `'Link8'` | 末端连杆 |
| `base_frame` | `'base_link'` | 坐标系原点 |
| `timeout.sec` | `5` | IK求解超时(秒) |
| error_code 1 | SUCCESS | 求解成功 |
| error_code -1 | FAILURE | 求解失败 |

## 🐛 调试技巧

```python
# 打印请求详情
self.get_logger().info(f"IK Request: {request}")

# 打印响应详情
self.get_logger().info(f"IK Solution: {response.solution.joint_state.position}")
self.get_logger().info(f"Error Code: {response.error_code.val}")

# 启用详细日志
rclpy.logging.set_logger_level('moveit_ros', rclpy.logging.LoggingSeverity.DEBUG)
```
