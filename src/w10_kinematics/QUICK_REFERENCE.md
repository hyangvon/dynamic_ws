# RViz IK 可视化 - 快速参考

## 🚀 启动（一行代码）

```bash
cd ~/ros2_ws/dynamic_ws && source install/setup.bash && \
ros2 launch w10_kinematics ik_visualize.launch.py
```

## ✅ 预期效果

- RViz 自动打开，显示 W10 机械臂 3D 模型
- 机械臂每 0.5 秒循环 4 种关节配置
- 终端打印每个状态的 EE 位置和臂角

## 📊 4 种演示状态

```
State 0 (0s-0.5s)   → 零配置（所有关节 0°）
State 1 (0.5s-1s)   → 肩部配置 (q2=0.3, q3=0.2, q4=-0.5)
State 2 (1s-1.5s)   → 弯曲配置 (q2=-0.3, q3=-0.2, q4=0.8)
State 3 (1.5s-2s)   → 腕部配置 (q2=0.2, q3=0.1, q4=-0.4, q5=0.3)
... 循环
```

## 🔧 RViz 不能自动配置时

### 方案 A：分别启动各组件（推荐用于调试）

```bash
# 终端 1
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat ~/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf)"

# 终端 2
cd ~/ros2_ws/dynamic_ws && source install/setup.bash && \
ros2 run w10_kinematics ik_visualize

# 终端 3
rviz2 -d ~/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/rviz/w10.rviz
```

### 方案 B：手动在 RViz 中配置

1. rviz2 打开后，左下角点击 "Add"
2. 按 "By display type" 
3. 找到 "RobotModel" 并点击
4. 设置 Description Topic: `/robot_description`
5. 重复步骤 1-4，添加 "TF" display
6. Save Config

## 📡 监测话题

```bash
# 查看发布的关节状态
ros2 topic echo /joint_states

# 查看节点
ros2 node list

# 查看话题图
rqt_graph
```

## 🎮 自定义配置

### 修改演示状态

编辑 `src/w10_kinematics/src/ik_visualize.cpp` - `timerCallback()` 函数

关键变量：
```cpp
q_solution(0)  // joint0
q_solution(1)  // joint1
q_solution(2)  // joint2
...
q_solution(10) // joint10
```

然后重新编译：
```bash
colcon build --packages-select w10_kinematics
```

### 修改循环周期

在 `IKVisualizer()` 构造函数中：
```cpp
timer_ = this->create_wall_timer(
    500ms,  // 改这个值（单位毫秒）
    std::bind(&IKVisualizer::timerCallback, this));
```

## ❌ 常见问题与快速解决

| 问题 | 快速解决 |
|------|---------|
| 看不到机械臂 | 添加 RobotModel display，设置 `/robot_description` |
| 机械臂不动 | 检查 `ros2 topic echo /joint_states` 有无数据 |
| TF 错误 | 添加 TF display，设置 Fixed Frame: `base_link` |
| Launch 失败 | 检查 `source install/setup.bash` |
| 节点崩溃 | 检查 URDF 路径是否正确 |

## 📂 关键文件

```
w10_kinematics/
├── src/
│   ├── ik_visualize.cpp     # 可视化节点
│   └── arm_angle_ik.cpp     # IK 算法
├── launch/
│   ├── ik_visualize.launch.py      # 自动 launch
│   └── start_ik_visualization.sh    # bash 脚本
└── include/
    └── arm_angle_ik.hpp     # IK 类定义
```

## 🔄 更新步骤

修改代码后：

```bash
cd ~/ros2_ws/dynamic_ws
colcon build --packages-select w10_kinematics
source install/setup.bash
ros2 launch w10_kinematics ik_visualize.launch.py
```

## 💾 录制演示

```bash
# 开始录制
ros2 bag record /joint_states -o my_demo

# 停止：按 Ctrl+C

# 回放
ros2 bag play my_demo
```

---

**详细文档：** 见 [RVIZ_IK_VISUALIZATION.md](./RVIZ_IK_VISUALIZATION.md)
