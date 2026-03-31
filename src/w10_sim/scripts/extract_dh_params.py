#!/usr/bin/env python3
"""
从w10.urdf提取DH (Denavit-Hartenberg) 参数
支持多种格式输出: CSV, MATLAB, Python, LaTeX表格
"""

import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation as R
import argparse
from pathlib import Path

def extract_dh_from_urdf(urdf_path):
    """从URDF文件提取DH参数"""
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    
    joints = []
    
    for joint in root.findall('.//joint'):
        name = joint.get('name')
        joint_type = joint.get('type')
        
        if name.startswith('joint'):
            origin = joint.find('origin')
            parent = joint.find('parent')
            child = joint.find('child')
            axis = joint.find('axis')
            
            if all([origin is not None, parent is not None, child is not None, axis is not None]):
                xyz = [float(x) for x in origin.get('xyz').split()]
                rpy = [float(x) for x in origin.get('rpy').split()]
                parent_link = parent.get('link')
                child_link = child.get('link')
                axis_xyz = [float(x) for x in axis.get('xyz').split()]
                
                # DH参数 (标准形式)
                d = xyz[2]  # 沿Z轴的偏移
                a = np.sqrt(xyz[0]**2 + xyz[1]**2)  # XY平面距离
                
                # 从RPY提取alpha
                rot = R.from_euler('xyz', rpy)
                mat = rot.as_matrix()
                alpha = np.arctan2(mat[2, 1], mat[2, 2])
                
                # theta通常为0 (初始位置)，由关节控制
                theta = 0.0
                
                joints.append({
                    'index': len(joints) + 1,
                    'name': name,
                    'parent': parent_link,
                    'child': child_link,
                    'type': joint_type,
                    'theta': theta,
                    'd': d,
                    'a': a,
                    'alpha': alpha,
                    'axis': axis_xyz,
                    'xyz': xyz,
                    'rpy': rpy,
                })
    
    return joints

def to_csv(joints, output_path=None):
    """导出为CSV格式"""
    lines = ["i,Joint_Name,theta(rad),d(m),a(m),alpha(rad),axis_x,axis_y,axis_z"]
    
    for j in joints:
        line = f"{j['index']},{j['name']},{j['theta']:.4f},{j['d']:.6f},{j['a']:.6f},{j['alpha']:.6f},{j['axis'][0]},{j['axis'][1]},{j['axis'][2]}"
        lines.append(line)
    
    content = "\n".join(lines)
    
    if output_path:
        Path(output_path).write_text(content)
        print(f"✓ CSV已保存: {output_path}")
    
    return content

def to_python(joints, output_path=None):
    """导出为Python字典格式"""
    code = "# w10机械臂 DH参数\n# 自动生成 - 需要手工验证\n\n"
    code += "DH_PARAMS = {\n"
    
    for j in joints:
        code += f"    '{j['name']}': {{\n"
        code += f"        'index': {j['index']},\n"
        code += f"        'theta': {j['theta']:.6f},  # Joint angle (rad) - 由运动规划确定\n"
        code += f"        'd': {j['d']:.6f},        # Link offset (m)\n"
        code += f"        'a': {j['a']:.6f},        # Link length (m)\n"
        code += f"        'alpha': {j['alpha']:.6f},  # Link twist (rad)\n"
        code += f"    }},\n"
    
    code += "}\n\n"
    code += "# DH变换矩阵 (标准形式)\n"
    code += "# T[i] = Rz(theta) * Tz(d) * Tx(a) * Rx(alpha)\n"
    
    if output_path:
        Path(output_path).write_text(code)
        print(f"✓ Python已保存: {output_path}")
    
    return code

def to_latex(joints, output_path=None):
    """导出为LaTeX表格"""
    latex = "\\begin{table}[h]\n"
    latex += "\\centering\n"
    latex += "\\caption{w10机械臂DH参数表}\n"
    latex += "\\begin{tabular}{|c|c|c|c|c|c|}\n"
    latex += "\\hline\n"
    latex += "关节 & $\\theta$ (rad) & $d$ (m) & $a$ (m) & $\\alpha$ (rad) & 轴向 \\\\\n"
    latex += "\\hline\n"
    
    for j in joints:
        axis = f"({j['axis'][0]:.0f}, {j['axis'][1]:.0f}, {j['axis'][2]:.1f})"
        latex += f"{j['name']} & {j['theta']:.3f} & {j['d']:.4f} & {j['a']:.4f} & {j['alpha']:.3f} & {axis} \\\\\n"
    
    latex += "\\hline\n"
    latex += "\\end{tabular}\n"
    latex += "\\end{table}\n"
    
    if output_path:
        Path(output_path).write_text(latex)
        print(f"✓ LaTeX已保存: {output_path}")
    
    return latex

def to_markdown(joints, output_path=None):
    """导出为Markdown表格"""
    md = "# w10机械臂DH参数表\n\n"
    md += "| 关节 | θ (rad) | d (m) | a (m) | α (rad) | 轴向 |\n"
    md += "|------|---------|-------|-------|---------|------|\n"
    
    for j in joints:
        axis = f"({j['axis'][0]:.0f}, {j['axis'][1]:.0f}, {j['axis'][2]:.1f})"
        md += f"| {j['name']} | {j['theta']:.4f} | {j['d']:.4f} | {j['a']:.4f} | {j['alpha']:.4f} | {axis} |\n"
    
    md += "\n## 说明\n"
    md += "- **θ (theta)**: 关节角度 (由运动规划确定，初始值=0)\n"
    md += "- **d**: 关节沿Z轴的偏移距离\n"
    md += "- **a**: 关节间链接长度\n"
    md += "- **α (alpha)**: 链接间的扭转角\n"
    md += "\n## DH坐标变换\n"
    md += "每个关节的齐次变换矩阵:\n"
    md += "$$T_i = R_z(\\theta_i) \\cdot T_z(d_i) \\cdot T_x(a_i) \\cdot R_x(\\alpha_i)$$\n"
    
    if output_path:
        Path(output_path).write_text(md)
        print(f"✓ Markdown已保存: {output_path}")
    
    return md

def main():
    parser = argparse.ArgumentParser(description='从URDF提取DH参数')
    parser.add_argument('--urdf', default='src/w10_sim/urdf/w10.urdf', help='URDF文件路径')
    parser.add_argument('--output', default='src/w10_sim', help='输出目录')
    parser.add_argument('--format', default='all', choices=['all', 'csv', 'py', 'latex', 'md'],
                        help='输出格式')
    args = parser.parse_args()
    
    print(f"[ 从 {args.urdf} 提取DH参数 ]\n")
    
    # 提取DH参数
    joints = extract_dh_from_urdf(args.urdf)
    
    # 打印到控制台
    print(f"检测到{len(joints)}个关节:\n")
    print(f"{'关节':<10} {'θ(rad)':<10} {'d(m)':<10} {'a(m)':<10} {'α(rad)':<12} {'轴向':<20}")
    print("-" * 80)
    for j in joints:
        axis = f"({j['axis'][0]:.0f},{j['axis'][1]:.0f},{j['axis'][2]:.1f})"
        print(f"{j['name']:<10} {j['theta']:<10.4f} {j['d']:<10.6f} {j['a']:<10.6f} {j['alpha']:<12.6f} {axis:<20}")
    
    print("\n" + "=" * 80)
    
    # 导出文件
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    if args.format in ['all', 'csv']:
        to_csv(joints, output_dir / 'dh_params.csv')
    
    if args.format in ['all', 'py']:
        to_python(joints, output_dir / 'dh_params.py')
    
    if args.format in ['all', 'latex']:
        to_latex(joints, output_dir / 'dh_params.tex')
    
    if args.format in ['all', 'md']:
        to_markdown(joints, output_dir / 'dh_params.md')
    
    print(f"\n✓ 所有文件已保存到: {output_dir}")

if __name__ == '__main__':
    main()
