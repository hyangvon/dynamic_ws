#!/bin/bash

# W10 IK Visualization 快速启动脚本

set -e

WORKSPACE="/home/user/ros2_ws/dynamic_ws"
cd "$WORKSPACE"

echo "======================================"
echo "  W10 机械臂 IK 可视化启动"
echo "======================================"
echo ""
echo "这个脚本会启动："
echo "  1. robot_state_publisher (TF 发布者)"
echo "  2. ik_visualize (IK 求解节点)"  
echo "  3. RViz (可视化工具)"
echo ""

# Source setup
source install/setup.bash

# Check if robot_state_publisher is available
if ! command -v robot_state_publisher &> /dev/null; then
    echo "⚠️  警告：robot_state_publisher 未安装"
    echo "   请运行：sudo apt install ros-humble-robot-state-publisher"
fi

# Check if rviz2 is available
if ! command -v rviz2 &> /dev/null; then
    echo "⚠️  警告：rviz2 未安装"
    echo "   请运行：sudo apt install ros-humble-rviz2"
fi

echo ""
echo "启动中..."
echo ""

# Start in background and capture PIDs
pids=()

# Start robot_state_publisher
echo "[1/3] 启动 robot_state_publisher..."
urdf_file="$WORKSPACE/install/w10_sim/share/w10_sim/urdf/w10.urdf"
if [ -f "$urdf_file" ]; then
    robot_state_publisher robot_state_publisher \
        --ros-args -p "robot_description:=$(cat $urdf_file)" &
    pids+=($!)
    sleep 1
else
    echo "❌ 错误：找不到 URDF 文件：$urdf_file"
    exit 1
fi

# Start ik_visualize
echo "[2/3] 启动 IK 可视化节点..."
ros2 run w10_kinematics ik_visualize &
pids+=($!)
sleep 2

# Start RViz
echo "[3/3] 启动 RViz..."
rviz_config="$WORKSPACE/install/w10_sim/share/w10_sim/rviz/w10.rviz"
if [ -f "$rviz_config" ]; then
    rviz2 -d "$rviz_config" &
    pids+=($!)
else
    echo "⚠️  未找到 RViz 配置文件，以默认配置启动..."
    rviz2 &
    pids+=($!)
fi

echo ""
echo "======================================"
echo "✅ 所有组件已启动！"
echo "======================================"
echo ""
echo "RViz 配置提示："
echo "  1. 在 RViz 中 Add 一个 RobotModel display"
echo "  2. 设置 Description Topic: /robot_description"
echo "  3. 在 RViz 中 Add 一个 TF display"
echo "  4. Fixed Frame 改为: base_link"
echo ""
echo "要停止所有进程，按 Ctrl+C"
echo ""

# Wait for all processes
wait

echo ""
echo "程序已停止。"
