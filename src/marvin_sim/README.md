# marvin_sim

`marvin_sim` 是一个用于 Marvin 机械手臂仿真的 ROS 2 包，支持变分积分器和结构保持基线算法。

## 功能

- 多种 C++ ROS 2 积分器节点：
  - `ctsvi_node` — 保守变分积分器基线
  - `atsvi_node` — 自适应变分积分器基线
  - `c_atsvi_node` — C-ATSVI 能量控制自适应积分器
- 提供 Marvin 机械臂的 URDF 和机器人描述
- 支持 ROS 2 启动文件用于仿真与 RViz 可视化
- 仿真结果导出为 CSV，以便后处理和分析
- Python 脚本辅助运行仿真、绘图与参数调试

## 包结构

- `src/` — C++ 节点源码
- `config/` — ROS 2 参数文件与绘图配置
- `launch/` — 仿真与 RViz 启动文件
- `urdf/` — 机器人模型文件
- `scripts/` — 分析、回放和仿真辅助脚本
- `csv/` — 按参数集合组织的仿真结果数据
- `fig/` — 分析脚本生成的图像

## 依赖项

该包依赖 ROS 2 以及以下软件包：

- `rclcpp`
- `std_msgs`
- `sensor_msgs`
- `robot_state_publisher`
- `joint_state_publisher_gui`
- `rviz2`
- `Eigen3`
- `pinocchio`
- `cppad`
- `coal`
- `launch_ros`

## 构建

在工作区根目录下执行：

```bash
cd ~/ros2_ws/dynamic_ws
colcon build --packages-select marvin_sim
source install/setup.bash
```

## 运行

### 运行单个仿真节点

使用包内参数文件 `src/marvin_sim/config/vi_params.yaml`：

```bash
ros2 run marvin_sim ctsvi_node --ros-args --params-file src/marvin_sim/config/vi_params.yaml
ros2 run marvin_sim atsvi_node --ros-args --params-file src/marvin_sim/config/vi_params.yaml
ros2 run marvin_sim c_atsvi_node --ros-args --params-file src/marvin_sim/config/vi_params.yaml
```

### 使用 RViz 启动仿真

```bash
ros2 launch marvin_sim sim_rviz.launch.py
```

该启动文件会启动：

- `robot_state_publisher`
- `ctsvi_node`
- `rviz2`

### 重放可视化

```bash
ros2 launch marvin_sim replay_rviz.launch.py
```

## 配置

主要仿真参数位于：

- `src/marvin_sim/config/vi_params.yaml`

关键字段包括：

- `q_init` — 初始关节角度（弧度）
- `timestep` — 积分步长
- `duration` — 仿真总时长
- `urdf_path` — 机器人 URDF 文件路径
- 外力参数（`force_enable`、`force_magnitude`、`force_dir_*` 等）
- `atsvi_node` 和 `c_atsvi_node` 的积分器专用参数

绘图配置文件位于：

- `src/marvin_sim/config/plot_config.yaml`

## 分析

运行仿真后，数据会写入包内的 CSV 目录：

- `src/marvin_sim/csv/<params>/<algorithm>/`

常见输出文件包括：

- `time_history.csv`
- `q_history.csv`
- `v_history.csv`
- `energy_history.csv`
- `delta_energy_history.csv`
- `momentum_history.csv`
- `ee_history.csv`

### 绘制结果

```bash
python3 src/marvin_sim/scripts/analyze_vi_results.py --path src/marvin_sim/csv/<params>/<algorithm>/ --plot
```

示例：

```bash
python3 src/marvin_sim/scripts/analyze_vi_results.py --path src/marvin_sim/csv/q0p059p2_dt0p05_T20_a0p4_b0p04/ctsvi_ad/ --plot
```

## 辅助脚本

- `scripts/vi_sim.py` — 方便的仿真节点启动脚本
- `scripts/analyze_vi_results.py` — 读取 CSV 数据并生成图像
- `scripts/replay_rviz.py` — 在 RViz 中回放仿真结果
- `scripts/tune_c_atsvi.py` — C-ATSVI 参数调优工具

## 注意事项

- 本包使用参数化输出目录布局，不同参数组合的仿真结果会分开保存。
- 当修改 `urdf_path` 或 `q_init` 后，需要重新生成仿真数据并重新分析。
- `package.xml` 中当前仍为占位许可证声明，后续可补充具体许可证信息。
