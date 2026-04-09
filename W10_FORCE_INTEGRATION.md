# w10_force 功能包集成指南

## 项目概述

`w10_force` 是一个新创建的 ROS 2 功能包，用于实现 W10 机械臂的力控制功能。该包已被配置为 `dynamic_ws` 的 git submodule，支持独立的 git 版本管理。

## 文件结构

```
src/w10_force/
├── .git/                           # w10_force 的独立 git 仓库
├── CMakeLists.txt                  # CMake 构建配置
├── package.xml                     # ROS 2 包描述文件
├── README.md                       # w10_force 包的详细文档
├── include/
│   └── w10_force/
│       └── force_controller.hpp    # 力控制器头文件
├── src/
│   ├── force_controller.cpp        # 力控制器实现
│   └── force_control_node.cpp      # ROS 2 力控制节点
└── launch/                         # 启动文件目录（预留）
```

## 依赖管理

### Package.xml 依赖配置

使用 `ament_cmake_auto` 实现自动依赖解决：

```xml
<buildtool_depend>ament_cmake_auto</buildtool_depend>
<depend>Eigen3</depend>
<depend>pinocchio</depend>
<depend>w10_sim</depend>
<depend>rclcpp</depend>
<depend>std_msgs</depend>
```

### CMakeLists.txt 配置

- 使用 `ament_auto_find_build_dependencies()` 自动发现和链接依赖
- 显式配置 Eigen3、pinocchio、rclcpp 等关键库

## Git Submodule 配置

### 远程仓库

- **本地 Bare 仓库**: `/tmp/git-repos/w10_force.git`
- **Submodule 路径**: `src/w10_force`
- **主分支**: `main`

### .gitmodules 配置

```ini
[submodule "src/w10_force"]
	path = src/w10_force
	url = /tmp/git-repos/w10_force.git
	branch = main
```

### .gitignore 配置

为了防止 w10_force 的 `.git` 目录被 dynamic_ws 追踪，在 `.gitignore` 中添加：

```
src/*/.git/
src/w10_force/.git/
```

## 构建和运行

### 构建单个包

```bash
cd ~/ros2_ws/dynamic_ws
colcon build --packages-select w10_force
```

### 构建所有包

```bash
colcon build
```

### 运行力控制节点

```bash
source install/setup.bash
ros2 run w10_force force_control_node
```

## Submodule 操作

### 克隆整个工作区（包括 submodule）

```bash
git clone --recurse-submodules <repo-url>
```

### 初始化现有仓库中的 submodules

```bash
git submodule update --init --recursive
```

### 更新 Submodule 到最新提交

```bash
cd src/w10_force
git pull origin main
cd ../..
git add src/w10_force
git commit -m "Update w10_force submodule"
```

### 在 w10_force 中提交更改

```bash
cd src/w10_force
git add .
git commit -m "your commit message"
git push origin main
cd ../..
git add src/w10_force
git commit -m "Update w10_force submodule reference"
```

## 关键特性

### 力控制器 (ForceController)

- **功能**: 计算基于期望力的关节扭矩
- **主要方法**:
  - `initialize()`: 从 URDF 初始化机器人模型
  - `computeForceTorque()`: 计算关节扭矩
  - `setDesiredForce()`: 设置期望的末端执行器力
  - `getTorques()`: 获取计算的扭矩

### 力控制节点 (ForceControlNode)

- ROS 2 节点包装力控制器
- 基于 rclcpp 框架实现
- 支持扩展为订阅和发布力控制相关话题

## 编译依赖

- **C++ 标准**: C++17（自动配置）
- **编译器**: GCC 或 Clang
- **主要库**:
  - Eigen3: 线性代数
  - Pinocchio: 机器人动力学计算
  - ROS 2: 分布式通信框架

## 后续扩展

1. **实现力控制算法**: 完成 `computeForceTorque()` 方法体
2. **添加启动文件**: 在 `launch/` 目录下创建节点启动文件
3. **添加参数配置**: 使用 ROS 2 参数系统配置控制参数
4. **单元测试**: 在构建测试中添加单元测试
5. **消息类型**: 根据需要扩展消息类型支持

## 故障排除

### 编译错误

如果遇到类似 `fatal error: xxx.hpp: No such file or directory` 的错误：

1. 确保所有依赖已安装
2. 检查 package.xml 中的依赖声明
3. 运行 `rosdep install --from-paths src --ignore-src -r -y`

### Submodule 问题

如果遇到 submodule 追踪问题：

```bash
# 重新初始化 submodule
git submodule deinit --all
git submodule update --init --recursive
```

## 许可证

Apache License 2.0

## 维护者

- user (hyang@buaa.edu.cn)
