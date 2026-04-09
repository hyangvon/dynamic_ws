#!/usr/bin/env python3
"""
根据DH参数生成规范的URDF文件
这个版本保证与Pinocchio AD引擎兼容
"""

import numpy as np
from pathlib import Path

def generate_urdf_from_dh(output_path='src/w10_sim/urdf/w10_canonical.urdf'):
    """根据DH参数生成Pinocchio兼容的URDF"""
    
    # w10的DH参数表
    # 格式: [theta, d, a, alpha]
    dh_table = [
        [0, 0.163, 0.0, 0],      # joint2
        [0, 0.085, 0.0, 0],      # joint3
        [0, 0.0001, 0.2815, 0],  # joint4
        [0, 0.1435, 0.0500, 0],  # joint5
        [0, 0.0000, 0.1213, 0],  # joint6
        [0, 0.3162, 0.0629, 0],  # joint7
        [0, 0.0620, 0.0684, 0],  # joint8
    ]
    
    joint_names = ['joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
    link_names = ['base_link', 'Link2', 'Link3', 'Link4', 'Link5', 'Link6', 'Link7', 'Link8']
    
    # 开始生成URDF
    urdf_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<!-- w10机械臂 - Pinocchio规范版本 -->',
        '<!-- 自动生成自DH参数 - 运动学规范 -->',
        '<robot name="w10_sim">',
        '',
    ]
    
    # 基座link
    urdf_lines.extend([
        '  <!-- 基座 -->',
        '  <link name="base_link">',
        '    <inertial>',
        '      <origin xyz="0 0 0.081676" rpy="0 0 0" />',
        '      <mass value="19.318" />',
        '      <inertia ixx="0.067819" ixy="0" ixz="0" iyy="0.067813" iyz="0" izz="0.04982" />',
        '    </inertial>',
        '    <visual>',
        '      <origin xyz="0 0 0" rpy="0 0 0" />',
        '      <geometry>',
        '        <box size="0.1 0.1 0.05" />',
        '      </geometry>',
        '      <material name="base">',
        '        <color rgba="0.5 0.5 0.5 1.0" />',
        '      </material>',
        '    </visual>',
        '  </link>',
        '',
    ])
    
    # 生成每个关节和链接
    for i, (dh, joint_name, link_name) in enumerate(zip(dh_table, joint_names, link_names[1:])):
        theta, d, a, alpha = dh
        parent = link_names[i]
        
        # 从DH参数计算xyz和rpy偏移
        # DH标准: T = Rz(θ) * Tz(d) * Tx(a) * Rx(α)
        # 初始位置时θ=0，所以:
        x = a
        y = 0
        z = d
        roll = alpha
        pitch = 0
        yaw = 0
        
        urdf_lines.extend([
            f'  <!-- {joint_name} 到 {link_name} -->',
            f'  <joint name="{joint_name}" type="revolute">',
            f'    <parent link="{parent}" />',
            f'    <child link="{link_name}" />',
            f'    <origin xyz="{x:.6f} {y:.6f} {z:.6f}" rpy="{roll:.6f} {pitch:.6f} {yaw:.6f}" />',
            f'    <axis xyz="0 0 1" />',  # 所有关节Z轴旋转
            f'    <limit lower="-3.14159" upper="3.14159" effort="100" velocity="1.0" />',
            f'    <dynamics damping="0.01" friction="0.01" />',
            f'  </joint>',
            '',
            f'  <link name="{link_name}">',
            f'    <inertial>',
            f'      <origin xyz="0 0 {d/2:.6f}" rpy="0 0 0" />',
            f'      <mass value="5.0" />',
            f'      <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.005" />',
            f'    </inertial>',
            f'    <visual>',
            f'      <origin xyz="0 0 0" rpy="0 0 0" />',
            f'      <geometry>',
            f'        <cylinder radius="0.02" length="{max(d, a, 0.1):.6f}" />',
            f'      </geometry>',
            f'      <material name="link">',
            f'        <color rgba="0.8 0.8 0.8 1.0" />',
            f'      </material>',
            f'    </visual>',
            f'  </link>',
            '',
        ])
    
    # 添加末端执行器
    urdf_lines.extend([
        '  <!-- 末端执行器 -->',
        '  <joint name="joint_tcp" type="fixed">',
        '    <parent link="Link8" />',
        '    <child link="tcp" />',
        '    <origin xyz="0 0 0.05" rpy="0 0 0" />',
        '  </joint>',
        '',
        '  <link name="tcp">',
        '    <inertial>',
        '      <origin xyz="0 0 0" rpy="0 0 0" />',
        '      <mass value="0.1" />',
        '      <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001" />',
        '    </inertial>',
        '    <visual>',
        '      <origin xyz="0 0 0" rpy="0 0 0" />',
        '      <geometry>',
        '        <sphere radius="0.01" />',
        '      </geometry>',
        '      <material name="tcp">',
        '        <color rgba="1.0 0.0 0.0 1.0" />',
        '      </material>',
        '    </visual>',
        '  </link>',
        '',
        '</robot>',
    ])
    
    urdf_content = '\n'.join(urdf_lines)
    
    # 保存文件
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(urdf_content)
    
    print(f"✓ 规范URDF已生成: {output_path}")
    print(f"\n说明:")
    print("- 所有关节都是Z轴旋转 (标准配置)")
    print("- RPY和xyz值计算自DH参数")
    print("- 使用简化的圆柱体几何 (不使用复杂mesh)")
    print("- 质量参数为估计值（需根据实际调整）")
    print("\n测试命令:")
    print(f"ros2 launch w10_sim ctsvi_w10.launch.py --ros-args -p urdf_path:={output_path}")

if __name__ == '__main__':
    generate_urdf_from_dh()
