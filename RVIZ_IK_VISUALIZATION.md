# RViz 中可视化 IK 求解结果

## 🚀 快速开始（3 步）

### 步骤1：打开一个终端

```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
```

### 步骤2：启动可视化（一行命令）

```bash
ros2 launch w10_kinematics ik_visualize.launch.py
```

✅ 直接进入 RViz，可以看到机械臂在四种不同的关节配置之间循环展示

---

## 📊 可视化效果

运行上面的命令后，您将看到：

1. **RViz窗口** - 显示 W10 机械臂的3D模型
2. **终端输出** - 显示每个状态的关节配置和末端执行器位置
3. **循环演示** - 机械臂每 0.5 秒在 4 种状态之间切换

### 4 个演示状态

| 状态 | 配置 | 说明 |
|------|------|------|
| **State 0** | 零配置 | 机械臂初始位置，所有关节角为 0 |
| **State 1** | q2=0.3, q3=0.2, q4=-0.5 | 肩部关节调整 |
| **State 2** | q2=-0.3, q3=-0.2, q4=0.8 | 机械臂弯曲 |
| **State 3** | q2=0.2, q3=0.1, q4=-0.4, q5=0.3 | 加入腕关节调整 |

---

## 🛠️ 故障排除

### 问题 1：RViz 中看不到机械臂

**解决方案：**

1. 确认 `robot_state_publisher` 正在运行
   ```bash
   ros2 node list | grep robot
   ```

2. 在 RViz 中手动添加 RobotModel display：
   - 左下角 "Add" 按钮
   - 选择 "By display type"
   - 找到 "RobotModel"
   - 设置 Description Topic: `/robot_description`

3. 添加 TF display：
   - "Add" → "TF"
   - 设置 Fixed Frame: `base_link`

### 问题 2：没看到运动变化

**检查项：**

1. 验证 `joint_states` 话题在发布：
   ```bash
   ros2 topic list | grep joint_states
   ```

2. 查看话题内容：
   ```bash
   ros2 topic echo /joint_states
   ```

3. 确保 RViz 订阅了正确的话题：
   - 在 RobotModel display 中检查 Description Topic

### 问题 3：RViz 显示转换错误

**检查转换树：**

```bash
# 列出所有可用的 TF frame
ros2 run tf2_tools view_frames.py
# 生成 frames.pdf，查看 TF 树结构
```

---

## 📝 RViz 手动配置步骤

如果自动配置不工作，按以下步骤手动配置：

### 1. 启动组件

**终端 1：**
```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat install/w10_sim/share/w10_sim/urdf/w10.urdf)"
```

**终端 2：**
```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
ros2 run w10_kinematics ik_visualize
```

**终端 3：**
```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
rviz2
```

### 2. 在 RViz 中配置

1. **添加 RobotModel**
   - 点击 "Add" → "By display type"
   - 选择 "RobotModel"
   - Description Topic: `/robot_description`

2. **添加 TF**
   - 点击 "Add" → "By display type"
   - 选择 "TF"  
   - Fixed Frame: `base_link`

3. **保存配置**
   - File → Save Config As
   - 命名为 `w10_ik.rviz`

---

## 🎮 监测和调试

### 查看所有发布的话题

```bash
ros2 topic list
```

### 订阅关节状态

```bash
ros2 topic echo /joint_states -n 1
```

输出示例：
```
header:
  stamp:
    sec: 1775028386
    nsec: 200151858
  frame_id: ''
name:
- joint0
- joint1
- joint2
...
position:
- 0.0
- 0.0
- 0.3
- 0.2
- -0.5
...
```

### 查看 ROS 2 节点

```bash
ros2 node list
```

期望看到：
- `/ik_visualizer` - IK 求解和数据发布
- `/robot_state_publisher` - TF 转换发布

### 查看节点之间的连接

```bash
rqt_graph
```

这将显示节点间的话题连接关系。

---

## 💡 自定义可视化

### 修改演示状态

编辑 `src/w10_kinematics/src/ik_visualize.cpp` 中的 `timerCallback()` 函数：

```cpp
case 0: {
  // 修改这里的关节配置
  Eigen::VectorXd q_solution = Eigen::VectorXd::Zero(ndof_);
  q_solution(2) = 0.5;   // joint2 = 0.5 rad
  q_solution(3) = 0.3;   // joint3 = 0.3 rad
  q_solution(4) = -0.7;  // joint4 = -0.7 rad
  // ...
}
```

然后重新编译：
```bash
colcon build --packages-select w10_kinematics
```

### 修改循环速度

在 `IKVisualizer::IKVisualizer()` 中修改定时器周期：

```cpp
timer_ = this->create_wall_timer(
    1000ms,  // 改为 1000ms（原来是 500ms）
    std::bind(&IKVisualizer::timerCallback, this));
```

### 修改关节名称

如果 W10 URDF 中的关节命名不同，修改：

```cpp
joint_names_ = {
  "your_joint0", "your_joint1", ...  // 对应你的 URDF
};
```

---

## 📊 录制和回放

### 录制关节状态

```bash
ros2 bag record /joint_states -o my_ik_demo
```

### 回放录制

```bash
ros2 bag play my_ik_demo
```

此时会在 RViz 中重现记录的运动。

---

## 🔍 常用 ROS 2 命令

| 命令 | 功能 |
|------|------|
| `ros2 topic list` | 列出所有话题 |
| `ros2 topic echo <topic>` | 查看话题内容 |
| `ros2 node list` | 列出所有节点 |
| `ros2 launch <pkg> <file.py>` | 启动 launch 文件 |
| `ros2 run <pkg> <exe>` | 运行可执行文件 |
| `rqt` | 启动 RQt GUI 工具 |
| `rqt_graph` | 显示节点和话题连接图 |

---

## 📦 相关文件位置

| 文件 | 位置 |
|------|------|
| IK 可视化节点 | `src/w10_kinematics/src/ik_visualize.cpp` |
| Launch 文件 | `src/w10_kinematics/launch/ik_visualize.launch.py` |
| 启动脚本 | `src/w10_kinematics/launch/start_ik_visualization.sh` |
| IK 算法 | `src/w10_kinematics/src/arm_angle_ik.cpp` |
| W10 URDF | `install/w10_sim/share/w10_sim/urdf/w10.urdf` |

---

## ✅ 验证一切正常

运行以下检查：

```bash
# 1. 检查包是否编译成功
ls -la ~/ros2_ws/dynamic_ws/build/w10_kinematics/ik_visualize

# 2. 检查 launch 文件
ls -la ~/ros2_ws/dynamic_ws/install/w10_kinematics/share/w10_kinematics/launch/

# 3. 检查 URDF 文件
cat ~/ros2_ws/dynamic_ws/install/w10_sim/share/w10_sim/urdf/w10.urdf | head -20

# 4. 运行简单测试
ros2 run w10_kinematics ik_visualize &
sleep 2
ros2 topic echo /joint_states -n 1
```

---

## 🎯 完整工作流

1. **打开终端** → 进入工作空间
2. **运行命令** → `ros2 launch w10_kinematics ik_visualize.launch.py`
3. **看到 RViz** → 机械臂应该出现并循环运动
4. **观察日志** → 在终端中看到每个状态的 IK 求解结果

---

**有问题？** 查看 [IK_DOCUMENTATION.md](./IK_DOCUMENTATION.md) 了解 IK 算法详情。
