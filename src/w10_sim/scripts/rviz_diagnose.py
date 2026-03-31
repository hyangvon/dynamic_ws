#!/usr/bin/env python3
"""
RViz显示问题诊断脚本
检查是否所有必要的条件都满足
"""

import subprocess
import time
import sys

def run_cmd(cmd, timeout=5):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "超时", -1

def check_roscore():
    """检查ROS是否正在运行"""
    output, code = run_cmd("pgrep -f roscore")
    return code == 0

def check_robot_description():
    """检查robot_description参数"""
    output, code = run_cmd("ros2 param get /robot_state_publisher robot_description 2>/dev/null | head -1")
    if code == 0 and "robot_description" in output:
        return True, "✓ robot_description 参数已设置"
    else:
        return False, "✗ robot_description 未设置（robot_state_publisher未运行？）"

def check_tf_topics():
    """检查TF话题是否发布"""
    output, code = run_cmd("ros2 topic list 2>/dev/null | grep -E '^/tf'")
    if "/tf" in output:
        return True, f"✓ TF话题: {output.strip()}"
    else:
        return False, "✗ 未发现TF话题"

def check_joint_states():
    """检查joint_states是否发布"""
    output, code = run_cmd("timeout 2 ros2 topic echo /joint_states 2>/dev/null | head -5")
    if code == 0 or "joint" in output:
        return True, "✓ joint_states 话题已发布"
    else:
        return False, "✗ 未发现joint_states话题（joint_state_publisher未运行？）"

def check_nodes():
    """检查必要的节点是否运行"""
    output, code = run_cmd("ros2 node list 2>/dev/null")
    nodes = output.split('\n')
    
    has_rsp = any('robot_state_publisher' in n for n in nodes)
    has_jsp = any('joint_state' in n for n in nodes)
    
    status = []
    if has_rsp:
        status.append("✓ robot_state_publisher 正在运行")
    else:
        status.append("✗ robot_state_publisher 未运行")
    
    if has_jsp:
        status.append("✓ joint_state_publisher 正在运行")
    else:
        status.append(f"⚠ joint_state_publisher 未运行 (可选)")
    
    return '\n  '.join(status)

def diagnose():
    """执行完整诊断"""
    print("\n" + "="*70)
    print("RViz可视化问题诊断")
    print("="*70)
    
    print("\n【步骤1】检查ROS环境...")
    rv, msg = check_robot_description()
    print(f"  {msg}")
    if not rv:
        print("  → 需要启动: ros2 launch w10_sim display_urdf_headless.launch.py")
    
    print("\n【步骤2】检查节点状态...")
    print(f"  {check_nodes()}")
    
    print("\n【步骤3】检查TF发布...")
    rv, msg = check_tf_topics()
    print(f"  {msg}")
    if not rv:
        print("  → robot_state_publisher可能未成功启动")
    
    print("\n【步骤4】检查关节状态...")
    rv, msg = check_joint_states()
    print(f"  {msg}")
    
    print("\n" + "="*70)
    print("【诊断结果】")
    print("="*70)
    
    # 检查是否可以启动RViz
    if "robot_description" in str(run_cmd("ros2 param list 2>/dev/null")[0]):
        print("\n✓ 可以启动RViz进行可视化")
        print("\n启动命令:")
        print("  rviz2 -d $(pwd)/install/w10_sim/share/w10_sim/rviz/w10.rviz")
    else:
        print("\n✗ 无法启动RViz - 缺少必要的节点")
        print("\n修复步骤:")
        print("1. 编译包:")
        print("   colcon build --packages-select w10_sim")
        print("\n2. 启动发布节点:")
        print("   source install/setup.bash")
        print("   ros2 launch w10_sim display_urdf_headless.launch.py")
        print("\n3. 在另一个终端启动RViz:")
        print("   rviz2")
    
    print("\n" + "="*70)
    print("\n【常见问题解决】\n")
    
    print("问题: RViz显示灰色窗口，没有机械臂")
    print("解决:")
    print("  1. 检查RViz的Fixed Frame是否为 'base_link'")
    print("  2. 点击左侧 'Add' 按钮")
    print("  3. 选择 'RobotModel'")
    print("  4. 在右侧面板设置:")
    print("     - Robot Description: robot_description")
    print("     - TF Prefix: (留空)")
    print("\n问题: 找不到机械臂，但能看到网格")
    print("解决:")
    print("  1. 尝试重置视图: View → Reset to Default")
    print("  2. 或者手动缩放: 滚轮或使用 'Zoom'")
    print("\n问题: 显示'不支持的消息类型'或类似错误")
    print("解决:")
    print("  1. RViz版本与ROS2版本不匹配")
    print("  2. 重启RViz")
    print("  3. 检查: ros2 --version")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    diagnose()
