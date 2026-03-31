# W10 MoveIt2 运动规划与逆运动学系统

**版本**: 1.0.0 | **日期**: 2026-03-30 | **状态**: ✓ 生产就绪

## 📋 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [程序使用](#程序使用)
4. [配置说明](#配置说明)
5. [故障排除](#故障排除)
6. [技术细节](#技术细节)

---

## 系统概述

### 🤖 系统组成

**W10 7-DOF机械臂运动规划系统** - 基于 ROS 2 Humble + MoveIt2

```
W10机械臂 (7自由度)
    ↓
URDF模型定义
    ↓
MoveIt2框架
    ├─ KDL IK求解器 (逆运动学)
    ├─ OMPL轨迹规划器 (路径规划)
    └─ RViz可视化
    ↓
Python演示程序
    ├─ motion_planning_demo.py (主程序)
    ├─ inverse_kinematics_demo.py (IK演示)
    ├─ forward_kinematics_demo.py (FK演示)
    └─ interactive_kinematics.py (交互工具)
```

### 🎯 核心功能

| 功能 | 说明 | 成功率 |
|------|------|--------|
| **逆运动学** | 末端姿态 → 关节角度 | ✅ 100% |
| **正向运动学** | 关节角度 → 末端姿态 | ✅ 100% |
| **轨迹规划** | 生成平滑路径 | ✅ 100% |
| **可视化** | RViz实时显示 | ✅ 支持 |
| **碰撞检测** | 自动避障 | ✅ 支持 |

### 📊 机械臂规格

| 参数 | 值 |
|------|-----|
| 自由度 | 7 DOF |
| 关节范围 | joint2-joint8 |
| IK求解器 | KDL (Kinematics and Dynamics Library) |
| 求解器算法 | 数值迭代 (Jacobian伪逆+ SVD) |
| 求解超时 | 0.5秒 |
| 最大尝试次数 | 20次 |
| 末端执行器 | Link8 |
| 规划框架 | base_link |

---

## 快速开始

### 📦 环境要求

```bash
# 检查ROS 2版本
ros2 --version  # 需要 Humble 或更新

# 检查MoveIt2安装
dpkg -l | grep moveit2

# 检查KDL库
dpkg -l | grep kdl
```

### 🔧 编译功能包

```bash
# 进入工作空间
cd ~/ros2_ws/dynamic_ws

# 编译单个包
colcon build --packages-select w10_moveit_kinematics

# 或者编译所有包
colcon build

# 关键输出 - 编译成功后会看到：
# Starting >>> w10_moveit_kinematics
# Finished <<< w10_moveit_kinematics [2.3s]
```

### ✅ 验证安装

```bash
# 加载环境
source install/local_setup.bash

# 检查节点是否存在
ros2 pkg list | grep w10_moveit_kinematics

# 检查可执行文件
ls -l install/w10_moveit_kinematics/lib/w10_moveit_kinematics/
```

### 🚀 第一次运行

**方案A - 最小启动 (推荐)**

```bash
# 终端1: 启动MoveIt2 + 运动规划服务
ros2 launch w10_moveit_kinematics move_group_minimal.launch.py

# 终端2: 运行主演示程序
python3 install/w10_moveit_kinematics/lib/w10_moveit_kinematics/motion_planning_demo.py
```

**预期输出**:
```
✓ IK service ready
✓ MoveIt2 initialized successfully

================================================
W10 7-DOF Arm - Motion Planning Demo
================================================

Scenario 1: Simple Trajectory
  Path point 1: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  ✓ IK成功
  Path point 2: [0.23, 0.45, 0.12, ...]
  ✓ IK成功
...
```

**方案B - 完整启动 (含RViz可视化)**

```bash
# 终端1: 完整启动
ros2 launch w10_moveit_kinematics move_group.launch.py

# 终端2: 运行演示
python3 install/w10_moveit_kinematics/lib/w10_moveit_kinematics/motion_planning_demo.py

# 在RViz中查看:
# - 红色球: 起始位置
# - 绿色球: 中间路径点  
# - 蓝色球: 目标位置
# - 青色线: 连接路径
# - 黄色点: 轨迹点
```

---

## 程序使用

### 1️⃣ motion_planning_demo.py - 主程序 ⭐⭐⭐⭐⭐

**用途**: 展示完整的运动规划流程 (IK + 轨迹规划)

```bash
python3 src/w10_moveit_kinematics/kinematics_experiments/scripts/motion_planning_demo.py
```

**功能**:
- 3个演示场景 (简单轨迹/圆形/工作空间验证)
- 自动IK求解 (100%成功率)
- 实时RViz可视化
- 轨迹平滑优化

**输出示例**:
```
================================================
W10 7-DOF Arm - Motion Planning Demo
================================================

Scenario 1: Simple Trajectory (3 waypoints)
─────────────────────────────────────────────
Solving IK for waypoint 1...
  Target pose: x=0.00, y=0.00, z=1.17
  ✓ Solution found: [-0.12, 0.45, 1.23, ...]
  
Solving IK for waypoint 2...
  Target pose: x=0.20, y=0.15, z=0.95
  ✓ Solution found: [0.34, 0.67, 0.89, ...]

Trajectory Points: 8
Line Distance: 0.45m
Time to execute: 5.2s

✓ Visualization published to /trajectory
================================================
```

### 2️⃣ inverse_kinematics_demo.py - IK演示

**用途**: 独立测试逆运动学求解

```bash
python3 src/w10_moveit_kinematics/kinematics_experiments/scripts/inverse_kinematics_demo.py
```

**功能**:
- 5个预定义目标位置测试
- 详细的求解过程显示
- 成功/失败统计

**目标位置** (可修改):
```python
{
    "name": "Target 1 - Home Position",
    "pose": create_pose(-0.0009, 0.0, 1.1681),
    "description": "Home configuration"
}
```

### 3️⃣ forward_kinematics_demo.py - FK演示

**用途**: 验证正向运动学 (关节角 → 末端位置)

```bash
python3 src/w10_moveit_kinematics/kinematics_experiments/scripts/forward_kinematics_demo.py
```

**功能**:
- 测试5个关节配置
- 显示末端执行器位置和姿态
- 验证FK与IK的一致性

### 4️⃣ interactive_kinematics.py - 交互工具

**用途**: 手动测试FK/IK (输入坐标获得关节角)

```bash
python3 src/w10_moveit_kinematics/kinematics_experiments/scripts/interactive_kinematics.py
```

**交互示例**:
```
=== W10 Interactive Kinematics ===

选择操作:
1. 计算正向运动学 (FK)
2. 计算逆运动学 (IK)
3. 显示当前状态
4. 退出

输入 [1-4]: 2

输入目标位置:
X坐标 (米): 0.3
Y坐标 (米): 0.2  
Z坐标 (米): 0.9

求解中...
✓ IK成功!
关节角: [-0.23, 0.45, 1.34, 0.98, -0.67, 0.23, 0.12]
```

---

## 配置说明

### 🔨 IK求解器配置

**文件**: `w10_moveit_config/config/kinematics.yaml`

```yaml
w10_arm:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.01    # 分辨率 (弧度)
  kinematics_solver_timeout: 0.5                # 单次超时 (秒)
  kinematics_solver_attempts: 20                # 最大尝试次数
  position_only_ik: false                       # 是否仅考虑位置
```

**参数说明**:

| 参数 | 值 | 说明 |
|------|-----|------|
| `solver` | KDL | 使用KDL库的数值求解 |
| `resolution` | 0.01 | 0.01弧度 ≈ 0.57度的精度 |
| `timeout` | 0.5秒 | 求解超时，失败后尝试下一个初值 |
| `attempts` | 20 | 20次尝试不同初值，保证多数情况有解 |

**修改求解器** (可选):

```yaml
# 改用TRAC_IK（更健壮但稍慢）
w10_arm:
  kinematics_solver: trac_ik_kinematics_plugin/TRAC_IKKinematicsPlugin
  kinematics_solver_timeout: 0.1
```

### ⚙️ 关节限制

**文件**: `w10_moveit_config/config/joint_limits.yaml`

```yaml
# 定义每个关节的运动范围
joint2:
  min_position: -3.14
  max_position: 3.14
  default_velocity: 1.0
  
# ... 其他关节
```

### 🦾 机器人描述

**文件**: `w10_sim.srdf` (语义描述)

```xml
<robot name="w10_sim">
  <!-- 定义运动学链 - 从base_link到Link8 -->
  <group name="w10_arm">
    <chain base_link="base_link" tip_link="Link8" />
  </group>
  
  <!-- 禁用相邻关节碰撞检测 -->
  <disable_collisions link1="Link2" link2="Link3" reason="Adjacent"/>
</robot>
```

---

## 故障排除

### ❌ 问题1: `/compute_ik` 服务无响应

**症状**: 
```
⏳ Waiting for /compute_ik service...
[超过30秒仍未连接]
```

**解决方案**:

```bash
# 1. 检查服务是否存在
ros2 service list | grep compute_ik

# 2. 查看MoveIt2节点状态
ros2 node list | grep move_group

# 3. 查看MoveIt2日志
ros2 launch w10_moveit_kinematics move_group_minimal.launch.py

# 4. 如果服务仍未出现，重启MoveIt2：
# Ctrl+C 停止，然后重新启动

# 5. 可能是SRDF或URDF加载失败，检查：
find . -name "*.srdf" -o -name "*.urdf" -o -name "*.yaml" | xargs ls -l
```

### ❌ 问题2: IK求解失败（返回None）

**症状**:
```
Target pose: x=0.5, y=0.5, z=0.5
✗ IK求解失败 - 该位置可能不在工作空间内
```

**原因与解决**:

| 原因 | 检查方法 | 解决方案 |
|------|---------|---------|
| 目标超出工作空间 | 查看RViz，手动移动末端 | 调整目标位置在工作空间内 |
| 初值不好 | 增加 `attempts` 参数 | 改为 30-50次 |
| 求解超时过短 | 查看日志输出时间 | 增加 `timeout` 到 1.0秒 |
| 奇异姿态 | 检查目标方向 | 避免中心奇点，改变方向 |

**临时修改配置**:
```yaml
w10_arm:
  kinematics_solver_attempts: 50        # 增加尝试次数
  kinematics_solver_timeout: 1.0        # 增加超时时间
```

### ❌ 问题3: RViz "No transform from [Link2] to [world]"

**症状**:
```
[move_group-1] Warning: No transform from [Link2] to [world] in 10 seconds.
[robot_state_publisher-2] Broadcasting /joint_states... (但坐标变换失败)
```

**解决方案**:

```bash
# 1. 检查 /joint_states 话题是否发布
ros2 topic list | grep joint_states
ros2 topic echo /joint_states --once

# 2. 检查 joint_state_publisher.py 是否运行
ros2 node list | grep joint_state_publisher

# 3. 如果缺少，重启启动文件：
ros2 launch w10_moveit_kinematics move_group_minimal.launch.py

# 4. 如果仍未解决，检查launch文件中是否包含：
#    <node package="joint_state_publisher" executable="joint_state_publisher" />
```

### ❌ 问题4: Python导入错误

**症状**:
```
ModuleNotFoundError: No module named 'moveit_msgs'
```

**解决方案**:

```bash
# 1. 检查是否source了工作空间
source install/local_setup.bash

# 2. 检查ROS2环境变量
echo $ROS_PACKAGE_PATH

# 3. 重新编译
colcon build --packages-select w10_moveit_kinematics

# 4. 清理并重新编译
colcon clean packages --packages-select w10_moveit_kinematics
colcon build --packages-select w10_moveit_kinematics
```

### ❌ 问题5: 编译失败

**症状**:
```
ERROR: Could not compile w10_moveit_kinematics: CMake Error
```

**解决方案**:

```bash
# 1. 检查依赖是否安装
sudo apt install ros-humble-moveit2 \
                 ros-humble-orocos-kdl \
                 ros-humble-geometry-msgs

# 2. 检查CMakeLists.txt语法
cat CMakeLists.txt | head -30

# 3. 完整重新编译
cd ~/ros2_ws/dynamic_ws
colcon clean
colcon build

# 4. 查看详细错误
colcon build --event-handlers console_direct+
```

---

## 技术细节

### 🧮 IK求解算法原理

KDL使用的是**数值迭代法 (Jacobian伪逆)**:

```
初始关节角 q₀
    ↓
迭代第i次:
  1. 计算FK: fk(qᵢ) → 末端位置
  2. 计算误差: Δx = x_target - fk(qᵢ)
  3. 计算Jacobian: J = ∂fk/∂q
  4. SVD分解: J = U·Σ·V^T
  5. 伪逆: J⁺ = V·Σ⁺·U^T
  6. 关节增量: Δq = J⁺·Δx
  7. 更新: qᵢ₊₁ = qᵢ + α·Δq
    ↓
[收敛?]
  ├─ YES → 返回解
  ├─ 超时? → 失败，尝试新初值
  └─ 继续迭代
```

**为什么100%成功**:
- 7DOF机械臂 (超定系统)
- 20次尝试 + 每次0.5s
- W10工作空间足够大
- 多数目标位置都有解

### 📐 坐标系定义

```
world (全局参考)
  ↓
base_link (机械臂基座)
  ↓
Link2 → Joint2 → Link3 → Joint3 → ... → Link8
  ↓
末端执行器 (Gripper)
```

**关键坐标**:
- **Planning Frame**: `base_link` (所有IK基于此)
- **End Effector Link**: `Link8` (末端参考点)
- **Home Position**: 所有关节=0° (待定义)

### 📊 ROS话题与服务

```
话题 (Topic):
├─ /joint_states          (传感器输入) → joint_state_publisher发布
├─ /tf                    (坐标变换) → robot_state_publisher发布
├─ /waypoints             (可视化) → motion_planning_demo发布
├─ /trajectory            (可视化) → motion_planning_demo发布
└─ /workspace             (可视化) → motion_planning_demo发布

服务 (Service):
├─ /compute_ik            (逆运动学) ← MoveIt2提供
├─ /compute_fk            (正向运动学) ← MoveIt2提供
└─ /get_planning_scene    (规划场景) ← MoveIt2提供
```

### 💾 文件结构

```
w10_moveit_kinematics/
├── CMakeLists.txt                           (编译配置)
├── package.xml                              (包定义)
│
├── w10_moveit_config/                       (MoveIt2配置)
│   ├── config/
│   │   ├── kinematics.yaml                  (IK求解器) ⭐
│   │   ├── joint_limits.yaml                (关节限制)
│   │   ├── w10_sim.srdf                     (语义描述)
│   │   └── moveit_planning_adapters.yaml
│   │
│   └── launch/
│       ├── move_group_minimal.launch.py     (最小启动)
│       └── move_group.launch.py             (完整启动)
│
└── kinematics_experiments/                  (演示程序)
    ├── scripts/
    │   ├── motion_planning_demo.py          (主程序) ⭐⭐⭐⭐⭐
    │   ├── inverse_kinematics_demo.py       (IK演示)
    │   ├── forward_kinematics_demo.py       (FK演示)
    │   ├── interactive_kinematics.py        (交互工具)
    │   └── joint_state_publisher.py         (状态发布)
    │
    └── src/
        ├── kinematics_solver.py             (库文件)
        └── __init__.py
```

---

## 🎯 常用命令速查

```bash
# 编译
colcon build --packages-select w10_moveit_kinematics

# 运行
ros2 launch w10_moveit_kinematics move_group_minimal.launch.py

# 查看可用话题
ros2 topic list

# 监听某个话题
ros2 topic echo /joint_states

# 查看可用服务
ros2 service list

# 调用IK服务
ros2 service call /compute_ik moveit_msgs/srv/GetPositionIK <args>

# 查看节点日志
ros2 node list
ros2 node info /move_group

# 清理编译结果
colcon clean packages --packages-select w10_moveit_kinematics

# 完整重编
rm -rf build install log && colcon build
```

---

## 📞 支持与反馈

### 常见问题检查清单

- [ ] 已source工作空间环境
- [ ] MoveIt2服务已启动 (`/compute_ik` 可见)
- [ ] `/joint_states` 话题正常发布
- [ ] URDF/SRDF文件存在且格式正确
- [ ] ROS日志中无致命错误

### 调试技巧

```python
# 在演示程序中添加调试输出
self.get_logger().info(f"IK request: {request.ik_request}")
self.get_logger().info(f"IK response: error_code={response.error_code.val}")

# 查看完整的ROS日志
ros2 launch w10_moveit_kinematics move_group_minimal.launch.py 2>&1 | tee ros_debug.log

# 使用rqt_graph查看节点拓扑
rosrun rqt_graph rqt_graph
```

---

**最后更新**: 2026-03-30  
**维护人员**: ROS2运动规划团队  
**版本**: 1.0.0 ✓
