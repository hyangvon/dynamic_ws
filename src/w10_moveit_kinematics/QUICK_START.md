# 快速开始指南 (Quick Start)

> ⏱️ 5分钟快速上手 W10 MoveIt2 运动规划系统

## 🚀 第一步：编译 (30秒)

```bash
cd ~/ros2_ws/dynamic_ws
colcon build --packages-select w10_moveit_kinematics
source install/local_setup.bash
```

## 🎯 第二步：启动 (选一种)

### 方案A: 最小启动 ⭐ 推荐

```bash
# 终端1
ros2 launch w10_moveit_kinematics move_group_minimal.launch.py

# 终端2  
python3 src/w10_moveit_kinematics/kinematics_experiments/scripts/motion_planning_demo.py
```

### 方案B: 包含RViz可视化

```bash
# 终端1
ros2 launch w10_moveit_kinematics move_group.launch.py

# 终端2
python3 src/w10_moveit_kinematics/kinematics_experiments/scripts/motion_planning_demo.py

# RViz中查看机械臂和轨迹（红/绿/蓝球 + 青色线 + 黄色点）
```

## ✅ 第三步：验证成功

看到这样的输出就成功了：

```
✓ IK service ready
================================================
W10 7-DOF Arm - Motion Planning Demo
================================================

Scenario 1: Simple Trajectory
  Solving IK for waypoint 1...
  ✓ Solution found: [0.12, 0.34, ...]
  Time: 0.15s
  
Scenario 2: Circle Trajectory  
  Solving IK for waypoint 1...
  ✓ Solution found: [...]
  
✓ All 3 scenarios completed successfully!
```

## 📝 其他演示程序

```bash
# 仅测试IK
python3 src/w10_moveit_kinematics/kinematics_experiments/scripts/inverse_kinematics_demo.py

# 仅测试FK  
python3 src/w10_moveit_kinematics/kinematics_experiments/scripts/forward_kinematics_demo.py

# 交互式工具（自己输入坐标）
python3 src/w10_moveit_kinematics/kinematics_experiments/scripts/interactive_kinematics.py
```

## ⚙️ 修改运动规划参数

编辑演示程序中的目标位置：

```python
# 文件: motion_planning_demo.py, 大约第350行

# 修改这里的waypoints
scenario1_waypoints = [
    self.create_pose(0.0, 0.0, 1.17),      # 修改X,Y,Z坐标
    self.create_pose(0.2, 0.1, 1.0),
    self.create_pose(0.3, 0.0, 0.9),
]
```

## 🔧 IK求解器配置

```yaml
# 文件: w10_moveit_config/config/kinematics.yaml

w10_arm:
  kinematics_solver_timeout: 0.5        # 改为 1.0 (若失败多)
  kinematics_solver_attempts: 20        # 改为 30-50 (若失败多)
```

## ❌ 常见问题速解

| 问题 | 解决方案 |
|------|---------|
| `/compute_ik` 服务无响应 | `ros2 service list \| grep compute_ik` 检查，或重启第一个终端 |
| IK求解失败 | 增加 `attempts` 或 `timeout` 参数 |
| RViz "No transform" 警告 | 重启程序，通常会自动恢复 |
| 编译失败 | `rm -rf build install && colcon build` 完整重编 |

## 📚 更多信息

详见: [详细使用说明](README-CN.md)

---

**核心参数速查**

```python
# motion_planning_demo.py 中可修改的关键参数

# 1. 目标位置 (X, Y, Z, 方向)
pose = self.create_pose(x=0.3, y=0.2, z=0.9, qx=0, qy=0, qz=-0.707, qw=0.707)

# 2. 中间插值点数
trajectory = self.create_trajectory(waypoints, num_intermediate=5)

# 3. 关节初始值 (home config)
self.home_config = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
```

**成功标志** ✓
- 所有IK求解成功 (✓标记)
- 可视化标记发布到RViz
- 轨迹点正确连接
- 无错误日志输出
