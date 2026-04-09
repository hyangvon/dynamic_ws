# W10 Kinematics - 臂角降维逆运动学求解器

## 项目概述

本功能包实现了针对W10机械臂的逆运动学（IK）求解器，采用**臂角降维**方法来处理机械臂的冗余自由度问题。

## 核心原理

### 臂角降维方法

臂角是指肩部（joint3）到腕部（末端执行器）的连线与水平面的夹角。通过约束臂角为特定值，可以将11自由度的IK问题降维为更低维的优化问题。

**臂角计算公式：**
$$\theta_{arm} = \arctan2(z_{ee} - z_{shoulder}, \sqrt{(x_{ee} - x_{shoulder})^2 + (y_{ee} - y_{shoulder})^2})$$

### 求解策略

1. **肩部位置：** Link3的位置（joint3之后）
2. **腕部位置：** 末端执行器的位置
3. **约束优化：** 在满足指定臂角的条件下，通过Jacobian方法迭代优化到目标位置

## 文件结构

```
w10_kinematics/
├── include/w10_kinematics/
│   └── arm_angle_ik.hpp           # 主求解器头文件
├── src/
│   ├── arm_angle_ik.cpp           # 求解器实现（正向运动学、臂角计算、IK求解）
│   └── ik_test.cpp                # 测试程序
├── CMakeLists.txt                 # 编译配置
├── package.xml                    # ROS2包描述
└── IK_DOCUMENTATION.md            # 本文档
```

## 核心类：ArmAngleIK

### 主要接口

#### 构造函数
```cpp
ArmAngleIK(const std::string& urdf_path);
```
从URDF文件加载机器臂模型。

#### 正向运动学
```cpp
bool forwardKinematics(const VectorXd& q, Eigen::Isometry3d& T_ee);
```
计算给定关节配置下的末端执行器位姿。

#### 臂角计算
```cpp
double getArmAngle(const VectorXd& q);
```
计算当前配置下的臂角（弧度）。

#### 逆运动学求解（臂角约束）
```cpp
bool solveIK(double arm_angle,
             const Vector3d& target_pos,
             const Eigen::Matrix3d& target_ori,
             const VectorXd& q_init,
             VectorXd& q_solution,
             double tol = 1e-6,
             int max_iter = 1000);
```

**参数：**
- `arm_angle`: 约束的臂角值（弧度）
- `target_pos`: 目标末端位置
- `target_ori`: 目标末端姿态（旋转矩阵）
- `q_init`: 初始关节配置
- `q_solution`: 返回的求解配置
- `tol`: 收敛精度（默认1e-6）
- `max_iter`: 最大迭代次数（默认1000）

## 编译和使用

### 编译
```bash
cd ~/ros2_ws/dynamic_ws
colcon build --packages-select w10_kinematics
```

### 运行测试
```bash
source install/setup.bash
ros2 run w10_kinematics ik_test
```

## 测试结果示例

```
========================================
   W10 Arm Angle Dimension Reduction IK
========================================
URDF: /home/user/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf

[ArmAngleIK] Model loaded from: ...
[ArmAngleIK] DOF: 11, Bodies: 8
[Test] Total DOF: 11
[Test] Total Bodies: 8

--- Test 1: Forward Kinematics (Zero Config) ---
Config: 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 
End-Effector Position: 0.0000 0.0000 0.7698
Arm Angle: 1.5708 rad (90.0000 deg)

--- Test 2: Forward Kinematics (Custom Config) ---
...

========================================
        All Tests Completed Successfully
========================================
```

## 关键技术细节

### 1. 正向运动学
- 基于Pinocchio库计算
- 支持复杂的链式机械臂模型
- 自动从URDF加载关节和链接信息

### 2. 臂角约束
- 通过调整腕部关节（joint7, joint8）来补偿臂角误差
- 补偿系数：`-0.1 * arm_angle_diff`
- 当臂角误差 > 0.01 rad时触发

### 3. IK求解算法
- **方法：** 阻尼最小二乘法（Damped Least Squares）
- **步长：** 0.1倍的梯度步
- **阻尼系数：** 0.01
- **收敛条件：** 位置误差 < 容差

## 依赖项

- **Eigen3**: 线性代数库
- **pinocchio**: 机器人动力学库
- **w10_sim**: W10机械臂模型定义

## 模型信息

- **总DOF数：** 11
- **总link数：** 8
- **基座链接：** base_link
- **末端执行器：** Link8（最后的link）

## 关节配置

| 关节 | 类型 | 范围 | 说明 |
|------|------|------|------|
| joint1 | - | - | 基座（无活动关节） |
| joint2 | 连续 | [-π, π] | 基座旋转 |
| joint3 | 转动 | [-1.8, 1.8] | 肩部关节 |
| joint4 | 转动 | 无限制 | 后臂关节 |
| joint5 | 转动 | 无限制 | 前臂关节 |
| joint6-8 | 转动 | 无限制 | 腕关节 |
| joint9-11 | 转动 | 无限制 | 指关节 |

## 算法流程

```
输入：臂角约束, 目标位置, 初始配置
输出：求解的关节配置

1. 初始化关节配置 q = q_init
2. 循环迭代：
   a. 计算正向运动学得到当前位姿
   b. 计算位置误差
   c. 如果误差 < 容差，收敛，返回成功
   d. 计算当前臂角和臂角误差
   e. 计算Jacobian矩阵
   f. 伪逆求解Δq
   g. 如果臂角误差显著，调整腕关节补偿
   h. 更新关节配置：q += 0.1 * Δq
   i. 施加关节限制
3. 如果达到最大迭代，返回失败
```

## 使用示例

```cpp
#include "w10_kinematics/arm_angle_ik.hpp"

// 创建求解器
w10_kinematics::ArmAngleIK ik_solver("/path/to/w10.urdf");

// 设置目标
Eigen::Vector3d target_pos(0.5, 0.0, 0.5);
Eigen::Matrix3d target_ori = Eigen::Matrix3d::Identity();
Eigen::VectorXd q_init = Eigen::VectorXd::Zero(11);
Eigen::VectorXd q_solution;

// 求解（臂角约束为0.2弧度）
bool success = ik_solver.solveIK(
    0.2,  // 臂角
    target_pos,
    target_ori,
    q_init,
    q_solution,
    1e-6,
    1000
);

if (success) {
    std::cout << "IK solution found: " << q_solution.transpose() << std::endl;
} else {
    std::cout << "IK failed to converge" << std::endl;
}
```

## 性能特性

- **求解时间：** 通常 < 1秒（1000次迭代内）
- **精度：** 位置误差可达 1e-6 米级别
- **可靠性：** 对初值敏感，推荐从零配置开始

## 已知限制

1. IK求解对初值敏感，可能陷入局部最优
2. 臂角约束是通过启发式方法实现，不是硬约束
3. 未考虑奇点处理和关节碰撞检测
4. 肩部位置的定义基于Link3frame，可能需要根据实际调整

## 扩展方向

- [ ] 实现多条件约束（例如同时约束位置、臂角、方向）
- [ ] 添加碰撞避免
- [ ] 优化求解速度
- [ ] 支持更多维度的约束
- [ ] 实现全局IK库集成

## 许可证

Apache License 2.0

## 参考资源

- Pinocchio文档：https://github.com/stack-of-tasks/pinocchio
- Eigen文档：https://eigen.tuxfamily.org/
- ROS 2文档：https://docs.ros.org/
