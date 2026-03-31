# w10机械臂 RViz可视化指南

## 🚀 快速开始

### 方法1：使用Headless模式 + 远程RViz（推荐）

**步骤1：在服务器上启动节点发布器**
```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
ros2 launch w10_sim display_urdf_headless.launch.py
```

**步骤2：在本地机器上启动RViz查看**
```bash
# 配置ROS_DOMAIN_ID（与服务器相同）
export ROS_DOMAIN_ID=0

# 启动RViz
rviz2

# 在RViz中：
# 1. 设置Fixed Frame为 "base_link"
# 2. 添加 "RobotModel" 显示插件
#    - Robot Description: robot_description
#    - TF Prefix: (留空)
# 3. 添加 "TF" 显示插件（显示坐标系）
```

---

### 方法2：直接启动带GUI的版本（本地机器）

如果你有图形界面和DISPLAY配置：

```bash
cd ~/ros2_ws/dynamic_ws
source install/setup.bash
ros2 launch w10_sim display_urdf.launch.py
```

这会自动启动3个窗口：
- **RViz** - 3D可视化
- **Joint State Publisher GUI** - 关节控制滑块
- **robot_state_publisher** - TF发布

---

### 方法3：手动启动各个组件

如果你想更细致地控制：

```bash
# 终端1：启动robot_state_publisher
ros2 launch w10_sim display_urdf_headless.launch.py

# 终端2：启动RViz
rviz2

# 终端3（可选）：手动发送关节命令
ros2 topic pub /joint_states sensor_msgs/JointState '{
  header: {stamp: now, frame_id: base_link},
  name: [joint2, joint3, joint4, joint5, joint6, joint7, joint8],
  position: [0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.0]
}' --once
```

---

## 🎮 在RViz中的操作

### 视图控制
- **鼠标中键 + 拖动** → 旋转视图
- **鼠标右键 + 拖动** → 平移视图
- **滚轮** → 缩放（放大/缩小）

### 关节控制（如果启动了GUI版本）
- 在 **Joint State Publisher GUI** 窗口中拖动滑块
- 机械臂会实时跟随关节角度变化
- 显示范围：-π ~ π (或根据URDF中的limit设置)

### 坐标系可视化
- 红线 (X轴) → X方向
- 绿线 (Y轴) → Y方向  
- 蓝线 (Z轴) → Z方向

---

## 📊 URDF选项

### 使用规范URDF（推荐）
```bash
ros2 launch w10_sim display_urdf.launch.py model:=$(pwd)/install/w10_sim/share/w10_sim/urdf/w10_canonical.urdf
```

### 使用原始URDF（有兼容性问题）
```bash
ros2 launch w10_sim display_urdf.launch.py model:=$(pwd)/install/w10_sim/share/w10_sim/urdf/w10.urdf
```

### 使用7_pendulum参考模型
```bash
ros2 launch w10_sim display_urdf.launch.py model:=$(pwd)/install/w10_sim/share/w10_sim/urdf/7_pendulum.urdf
```

---

## 🔧 故障排除

### 错误：RViz启动失败 / Joint State Publisher GUI崩溃
**原因**：Headless环境（无DISPLAY/图形界面）

**解决方案**：
```bash
# 使用headless版本
ros2 launch w10_sim display_urdf_headless.launch.py

# 然后在本地机器上用远程RViz连接
# 或使用SSH X11转发
ssh -X user@remote_machine
rviz2
```

### 错误：无法连接到robot_description
**原因**：robot_state_publisher未启动或URDF加载失败

**检查**：
```bash
# 查看是否有robot_description参数
ros2 param get /robot_state_publisher robot_description

# 查看TF树
ros2 run tf2_tools view_frames.py
ps2_ps aux | grep robot_state_publisher
```

### RViz中看不到机械臂
**检查清单**：
1. ✓ Fixed Frame设置为 "base_link"
2. ✓ 添加了 "RobotModel" 显示插件
3. ✓ Robot Description参数设置为 "robot_description"
4. ✓ TF Prefix留空
5. ✓ 运行 `ros2 topic list` 确认有 `/tf` 和 `/tf_static` 话题

---

## 💾 生成URDF可视化快照

### 保存RViz配置
```bash
# 在RViz中调整好视图后，File → Save Config As
# 保存位置：src/w10_sim/rviz/w10_custom.rviz
```

### 导出3D视图为图片
```bash
# 使用RViz内置功能
# 在RViz菜单: Tools → Take Snapshot
# 或命令行方式
rviz2 -d $(pwd)/install/w10_sim/share/w10_sim/rviz/w10.rviz --screenshot-dir=/tmp/ --screenshot-format png
```

---

## 📝 launch文件说明

### display_urdf.launch.py（带GUI）
- **组件**：robot_state_publisher + joint_state_publisher_gui + rviz2
- **用途**：本地完整可视化和交互
- **依赖**：图形界面 (DISPLAY变量)

### display_urdf_headless.launch.py（无GUI）
- **组件**：robot_state_publisher + joint_state_publisher
- **用途**：服务器运行，远程查看
- **优点**：无图形界面依赖，轻量级

---

## 🔗 相关命令速查

```bash
# 查看发布的话题
ros2 topic list | grep -E "joint|tf|robot"

# 查看joint_states消息
ros2 topic echo /joint_states

# 查看TF树
ros2 run tf2_tools view_frames.py
evince frames.pdf

# 手动设置关节角度
ros2 service call /set_pose geometry_msgs/Pose '{position: {x: 0, y: 0, z: 0.5}, orientation: {x: 0, y: 0, z: 0, w: 1}}'

# 启动RViz并加载配置
rviz2 -d $(pwd)/install/w10_sim/share/w10_sim/rviz/w10.rviz

# 查看robot_description内容
ros2 param get /robot_state_publisher robot_description | head -50
```

---

## ⚙️ 高级配置

### 修改RViz默认配置
编辑 `src/w10_sim/rviz/w10.rviz` 文件来自定义：
- 背景颜色
- 网格大小
- 摄像头视角
- 显示的tf坐标系

### 创建自定义RViz配置
1. 手动调整RViz窗口
2. 保存配置：File → Save Config As
3. 指定配置文件启动：
   ```bash
   ros2 launch w10_sim display_urdf.launch.py rviz_config:=$(pwd)/my_config.rviz
   ```

---

## 📚 有用资源

- [ROS2 RViz文档](https://docs.ros.org/en/humble/Tutorials/Intermediate/RViz2/RViz2-Main.html)
- [URDF形成文档](http://wiki.ros.org/urdf)
- [robot_state_publisher文档](https://docs.ros.org/en/humble/p/robot_state_publisher/)
- [joint_state_publisher文档](https://docs.ros.org/en/humble/p/joint_state_publisher/)

---

**最后更新**: 2026-03-31  
**工具版本**: ROS2 Humble, RViz2
