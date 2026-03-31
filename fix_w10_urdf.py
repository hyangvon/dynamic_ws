#!/usr/bin/env python3
"""
修复w10.urdf中的RPY数值误差问题
将所有±1.5707963...简化为±π/2的精确值
"""

import re
import numpy as np

# 读取原始URDF
with open('src/w10_sim/urdf/w10.urdf', 'r') as f:
    content = f.read()

# π/2的精确值
PI_2 = 1.5707963267948966

# 替换规则：将带浮点误差的RPY转换为标准值
replacements = [
    # joint3: -1.5708 0 -1.5708 → 保持，但用标准π/2值
    (r'(joint3.*?rpy=")[^"]*"', 
     lambda m: m.group(1) + f"{-PI_2} 0 {-PI_2}" + '"'),
    
    # joint4: 1.5708 0 0 → 保持
    (r'(joint4.*?rpy=")[^"]*"',
     lambda m: m.group(1) + f"{PI_2} 0 0" + '"'),
    
    # joint5: -1.5708 0 0 → 保持  
    (r'(joint5.*?rpy=")[^"]*"',
     lambda m: m.group(1) + f"{-PI_2} 0 0" + '"'),
    
    # joint6: 1.5708 0 0 → 保持
    (r'(joint6.*?rpy=")[^"]*"',
     lambda m: m.group(1) + f"{PI_2} 0 0" + '"'),
    
    # joint7: -1.5708 0 0 → 保持
    (r'(joint7.*?rpy=")[^"]*"',
     lambda m: m.group(1) + f"{-PI_2} 0 0" + '"'),
    
    # joint8: 1.5708 0 0 → 保持
    (r'(joint8.*?rpy=")[^"]*"',
     lambda m: m.group(1) + f"{PI_2} 0 0" + '"'),
]

# 执行替换
original = content
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 显示变更
print("修复w10.urdf - 标准化RPY浮点值")
print("=" * 70)

# 提取修改前后的joint3作为示例
print("\n修改前 joint3:")
match_old = re.search(r'<joint\s+name="joint3".*?rpy="([^"]*)"', original, re.DOTALL)
if match_old:
    print(f"  rpy=\"{match_old.group(1)}\"")

print("\n修改后 joint3:")
match_new = re.search(r'<joint\s+name="joint3".*?rpy="([^"]*)"', content, re.DOTALL)
if match_new:
    print(f"  rpy=\"{match_new.group(1)}\"")

# 备份并保存
import shutil
shutil.copy('src/w10_sim/urdf/w10.urdf', 'src/w10_sim/urdf/w10.urdf.bak')
print("\n\\n✓ 已备份原文件为: w10.urdf.bak")

with open('src/w10_sim/urdf/w10.urdf', 'w') as f:
    f.write(content)

print("✓ 已保存修复后的w10.urdf")
print("\\n下一步: 重新编译并测试")
print("  colcon build --packages-select w10_sim")
print("  ros2 launch w10_sim ctsvi_w10.launch.py")
