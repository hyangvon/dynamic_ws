# IK 可视化使用指南

## 快速开始

### 方法1：使用 Launch 文件（推荐）

在一个终端中运行：

```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
ros2 launch w10_kinematics ik_visualize.launch.py
```

这将自动启动：
- **robot_state_publisher**：将关节状态转换为 TF 变换
- **ik_visualize**：执行 IK 求解并发布关节状态
- **RViz**：可视化机械臂

### 方法2：手动启动各组件

如果想要更多控制，可以在多个终端中分别启动：

**终端1 - 启动 IK 可视化节点：**

```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
ros2 run w10_kinematics ik_visualize
```

**终端2 - 启动 robot_state_publisher：**

```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat install/w10_sim/share/w10_sim/urdf/w10.urdf)"
```

**终端3 - 启动 RViz2：**

```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
rviz2 -d install/w10_sim/share/w10_sim/rviz/w10.rviz
```

## RViz 配置

如果RViz没有自动显示机械臂，按下列步骤手动配置：

1. **添加 RobotModel**
   - 点击 "Add" 按钮
   - 选择 "By display type"
   - 找到 "RobotModel" 并添加
   - 设置 Description Topic：`/robot_description`

2. **配置 TF**
   - 点击 "Add" 按钮  
   - 选择 "By display type"
   - 找到 "TF" 并添加
   - Ensure fixed frame 设为 `base_link` 或相应的基座frame

3. **保存配置**
   - File → Save Config As
   - 命名为 `w10_rviz.rviz`

## 监控话题和日志

**查看发布的关节状态：**

```bash
ros2 topic echo /joint_states
```

**查看 IK 求解日志：**

```bash
# 在运行 ik_visualize 的终端中可以看到详细日志
# 例如：
# [ik_visualizer-1] [INFO] [1743523200.123456789] [ik_visualizer]: 
#   === State 0: IK to position [0, 0, 0.7] ===
# [ik_visualizer-1] [INFO] [1743523200.234567890] [ik_visualizer]: 
#   EE Position: [0.0000, 0.0000, 0.7000]
```

## 实验结果解读

IK 可视化节点会循环执行以下 4 个状态（每 0.5 秒切换一次）：

**状态 0**：位置 [0, 0, 0.7] m
- 目标臂角：0.5 rad (28.65°)
- 机械臂会展开到该目标位置

**状态 1**：位置 [0.1, 0, 0.65] m  
- 目标臂角：0.3 rad (17.19°)
- 机械臂向前和向下移动

**状态 2**：位置 [-0.1, 0, 0.6] m
- 目标臂角：0.0 rad (0°)
- 机械臂向后和向下移动

**状态 3**：零配置
- 所有关节回到初始位置

## 常见问题

**Q: RViz 中没看到机械臂？**  
A: 检查：
1. 确认 `robot_state_publisher` 已运行
2. 在 RViz 中检查 Error 面板，查看转换错误
3. 检查 Fixed Frame 设置是否正确

**Q: 机械臂姿态不对？**  
A: 确认：
1. W10 URDF 路径正确
2. 关节名称匹配（joint0-joint10）
3. `joint_states` 话题正在发布

**Q: 如何修改 IK 目标位置？**  
A: 编辑 `src/ik_visualize.cpp` 中的 `timerCallback()` 函数，修改 `target_pos` 和 `arm_angle` 值，然后重新编译。

**Q: 如何改变循环速度？**  
A: 在 `IKVisualizer::IKVisualizer()` 中修改 `500ms` 的值（单位：毫秒）。

## 使用 ros2 bag 录制实验

```bash
# 录制
ros2 bag record /joint_states -o ik_experiment

# 回放
ros2 bag play ik_experiment
```

## 代码位置

- **可视化节点**：`src/w10_kinematics/src/ik_visualize.cpp`
- **Launch 文件**：`src/w10_kinematics/launch/ik_visualize.launch.py`
- **IK 求解器**：`src/w10_kinematics/src/arm_angle_ik.cpp`

## 进阶：自定义 IK 目标

编辑 `src/w10_kinematics/src/ik_visualize.cpp` 的 `timerCallback()` 函数：

```cpp
case 0: {
  // 修改这里的目标位置和臂角
  Eigen::Vector3d target_pos(0.2, 0.1, 0.65);  // 新的目标位置 [x, y, z]
  double arm_angle = 0.7;  // 新的臂角约束 [rad]
  // ... 其余代码不变
}
```

然后重新编译：

```bash
colcon build --packages-select w10_kinematics
```
