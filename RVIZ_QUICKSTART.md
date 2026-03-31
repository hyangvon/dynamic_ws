# 🚀 w10机械臂RViz可视化 - 5分钟快速开始

## 方案选择

### ✅ 推荐方案：Headless + 远程RViz

**优点**：
- 无图形界面依赖
- 跨机器可视化
- 在远程服务器上运行，本地显示

**步骤**：

```bash
# 【服务器端】终端1: 启动节点发布器
cd ~/ros2_ws/dynamic_ws && source install/setup.bash
ros2 launch w10_sim display_urdf_headless.launch.py

# 【本地机器】终端2: 启动RViz查看
export ROS_DOMAIN_ID=0
rviz2
```

在RViz中：
1. 左侧面板 → Add → RobotModel
2. Robot Description 输入：`robot_description`
3. 右侧即可看到w10机械臂

---

## 🎮 实时控制关节（三选一）

### 方案A：使用Python脚本（推荐学习）

```bash
# 终端3: 移动到HOME位置
ros2 run w10_sim w10_joint_controller.py home

# 移动到演示配置
ros2 run w10_sim w10_joint_controller.py config --config demo1

# 连续扫动所有关节
ros2 run w10_sim w10_joint_controller.py sweep --amplitude 0.5 --period 4.0 --duration 10.0
```

### 方案B：使用Joint State Publisher GUI

```bash
# 如果本地有X11显示
ros2 launch w10_sim display_urdf.launch.py
# 自动打开Joint State Publisher GUI窗口，拖动滑块控制
```

### 方案C：手动发送ROS消息

```bash
ros2 topic pub /joint_states sensor_msgs/JointState '{
  header: {stamp: now, frame_id: base_link},
  name: [joint2, joint3, joint4, joint5, joint6, joint7, joint8],
  position: [0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.0]
}' --once
```

---

## 📂 可视化文件位置

```
src/w10_sim/
├── launch/
│   ├── display_urdf.launch.py           ← 带GUI版本
│   └── display_urdf_headless.launch.py  ← 无GUI版本（推荐）
├── rviz/
│   └── w10.rviz                         ← RViz配置文件
├── scripts/
│   ├── w10_joint_controller.py          ← 关节控制脚本
│   ├── extract_dh_params.py             ← DH参数提取
│   └── analyze_vi_results.py            ← 仿真结果分析
├── urdf/
│   ├── w10_canonical.urdf               ← 规范URDF（推荐）
│   └── w10.urdf                         ← 原始URDF
└── dh_params.md                         ← DH参数表
```

---

## 🔗 快速命令

```bash
# 所有一步到位（本地机器）
source ~/ros2_ws/dynamic_ws/install/setup.bash
ros2 launch w10_sim display_urdf.launch.py

# 查看TF树
ros2 run tf2_tools view_frames.py && evince frames.pdf

# 列出所有可用话题
ros2 topic list

# 监听joint_states消息
ros2 topic echo /joint_states

# 查看robot_description参数
ros2 param get /robot_state_publisher robot_description | head -20
```

---

## ⚠️ 常见问题

**Q: RViz无法显示机械臂？**
- ✓ 检查Fixed Frame是否为 "base_link"
- ✓ 添加RobotModel插件，robot_description参数设为"robot_description"
- ✓ 运行 `ros2 topic list | grep tf` 确认有tf话题

**Q: 远程连接找不到自己的机器？**
- ✓ 确保ROS_DOMAIN_ID相同
- ✓ 确保网络能互通（ping一下）
- ✓ 检查防火墙 (ROS2使用UDP 7400-7410端口)

**Q: 启动时出现"DISPLAY"相关错误？**
- 这是headless环境，使用：`ros2 launch w10_sim display_urdf_headless.launch.py`

---

## 📚 完整文档

详细文档请查看：
- [RVIZ_GUIDE.md](./src/w10_sim/RVIZ_GUIDE.md) - 完整RViz指南
- [W10_DH_GUIDE.md](./W10_DH_GUIDE.md) - DH参数和URDF说明

---

**现在就试试吧！** 🎉

```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
ros2 launch w10_sim display_urdf_headless.launch.py
```

然后在另一个终端：
```bash
rviz2
```

