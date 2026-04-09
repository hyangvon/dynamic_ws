#!/usr/bin/env python3
"""
w10 VI Node 仿真结果分析脚本

用法：
    # 单个CSV目录
    python3 analyze_vi_results.py --path src/w10_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/ctsvi_ad/
    
    # 多个子文件夹（会自动处理所有子文件夹）
    python3 analyze_vi_results.py --path src/w10_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/
    
    # 显示图表
    python3 analyze_vi_results.py --path src/w10_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/ --plot
    
    # 自定义配置文件
    python3 analyze_vi_results.py --path src/w10_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/ --config config/plot_config.yaml
    
    # 自定义保存路径
    python3 analyze_vi_results.py --path src/w10_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/ --save-plot /tmp/output.png

配置文件：
    - 默认配置文件位置: src/w10_sim/config/plot_config.yaml
    - 在配置文件中可以为各个图表指定固定的坐标轴范围
    - 设置为 null 表示自动调整（根据数据自动设置范围）
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import sys
import yaml

def load_plot_config(config_path=None):
    """加载绘图配置文件"""
    if config_path is None:
        # 尝试从默认位置查找配置文件
        default_paths = [
            Path('src/w10_sim/config/plot_config.yaml'),
            Path('config/plot_config.yaml'),
            Path(__file__).parent.parent / 'config' / 'plot_config.yaml',
        ]
        for path in default_paths:
            if path.exists():
                config_path = path
                break
    
    config = {}
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            print(f"✓ 已加载绘图配置: {config_path}")
        except Exception as e:
            print(f"⚠ 警告: 无法加载配置文件 {config_path}: {e}")
    else:
        print("⚠ 未找到绘图配置文件，使用默认配置（自动调整范围）")
    
    return config

def load_data(csv_dir):
    """加载所有CSV数据"""
    csv_dir = Path(csv_dir)
    
    data = {}
    
    # 加载时间
    time_file = csv_dir / 'time_history.csv'
    if time_file.exists():
        data['time'] = np.loadtxt(time_file)
    
    # 加载能量
    e_file = csv_dir / 'energy_history.csv'
    if e_file.exists():
        data['energy'] = np.loadtxt(e_file)
    
    # 加载能量分量
    et_file = csv_dir / 'energy_T_history.csv'
    if et_file.exists():
        data['energy_T'] = np.loadtxt(et_file)
    
    eu_file = csv_dir / 'energy_U_history.csv'
    if eu_file.exists():
        data['energy_U'] = np.loadtxt(eu_file)
    
    # 加载能量漂移
    de_file = csv_dir / 'delta_energy_history.csv'
    if de_file.exists():
        data['delta_energy'] = np.loadtxt(de_file)
    
    # 加载关节配置
    q_file = csv_dir / 'q_history.csv'
    if q_file.exists():
        q_raw = np.loadtxt(q_file, delimiter=',')
        # 1-DOF case: np.loadtxt returns 1D array, reshape to (N, 1)
        if q_raw.ndim == 1:
            q_raw = q_raw.reshape(-1, 1)
        data['q'] = q_raw
    
    # 加载末端位置
    ee_file = csv_dir / 'ee_history.csv'
    if ee_file.exists():
        data['ee'] = np.loadtxt(ee_file, delimiter=',')
    
    # 加载动量
    p_file = csv_dir / 'momentum_history.csv'
    if p_file.exists():
        p_raw = np.loadtxt(p_file, delimiter=',')
        if p_raw.ndim == 1:
            p_raw = p_raw.reshape(-1, 1)
        data['momentum'] = p_raw
    
    # 加载执行时间
    rt_file = csv_dir / 'avg_runtime.txt'
    if rt_file.exists():
        data['avg_runtime'] = float(np.loadtxt(rt_file))
    
    return data

def print_summary(data, csv_dir, subfolder_name=None):
    """打印仿真统计信息"""
    print(f"\n{'='*60}")
    print(f"Simulation Results Summary")
    if subfolder_name:
        print(f"Subfolder: {subfolder_name}")
    print(f"Directory: {csv_dir}")
    print(f"{'='*60}\n")
    
    if 'time' in data:
        time = data['time']
        print(f"Simulation Duration: {time[-1]:.3f} s ({len(time)} steps)")
        dt = time[1] - time[0] if len(time) > 1 else 0
        print(f"Timestep: {dt:.6f} s")
    
    if 'energy' in data:
        energy = data['energy']
        print(f"\nEnergy Statistics:")
        print(f"  Initial Energy:     {energy[0]:>15.6f} J")
        print(f"  Final Energy:       {energy[-1]:>15.6f} J")
        print(f"  Mean Energy:        {np.mean(energy):>15.6f} J")
        print(f"  Energy Std Dev:     {np.std(energy):>15.6f} J")
    
    if 'delta_energy' in data:
        de = data['delta_energy']
        print(f"\nEnergy Drift:")
        print(f"  Max Drift:          {np.max(np.abs(de)):>15.6f} J")
        print(f"  Relative Drift:     {np.max(np.abs(de))/np.max(np.abs(data['energy']))*100:>14.4f} %")
    
    if 'energy_T' in data and 'energy_U' in data:
        T = data['energy_T']
        U = data['energy_U']
        print(f"\nKinetic/Potential Energy:")
        print(f"  Peak Kinetic:       {np.max(T):>15.6f} J")
        print(f"  Peak Potential:     {np.max(U):>15.6f} J")
    
    if 'avg_runtime' in data:
        print(f"\nComputational Performance:")
        print(f"  Avg Step Time:      {data['avg_runtime']:>15.3f} ms")
    
    if 'ee' in data:
        ee = data['ee']
        print(f"\nEnd-Effector Position:")
        print(f"  Initial: [{ee[0, 0]:.4f}, {ee[0, 1]:.4f}, {ee[0, 2]:.4f}]")
        print(f"  Final:   [{ee[-1, 0]:.4f}, {ee[-1, 1]:.4f}, {ee[-1, 2]:.4f}]")
        ee_dist = np.linalg.norm(ee[-1] - ee[0])
        print(f"  Total Displacement: {ee_dist:.4f} m")
    
    print(f"\n{'='*60}\n")

def plot_results(data, config=None):
    """绘制仿真结果
    
    参数：
        data: 加载的仿真数据
        config: 绘图配置字典（来自plot_config.yaml）
    """
    if config is None:
        config = {}
    
    time = data.get('time', np.arange(len(data.get('energy', []))))
    
    # 获取各项配置（如果不存在则为None，表示自动调整）
    cfg_energy = config.get('energy', {}) or {}
    cfg_delta_e = config.get('delta_energy', {}) or {}
    cfg_ee_pos = config.get('end_effector_position', {}) or {}
    cfg_ee_speed = config.get('end_effector_speed', {}) or {}
    cfg_joints = config.get('joint_configuration', {}) or {}
    cfg_traj3d = config.get('trajectory_3d', {}) or {}
    
    fig = plt.figure(figsize=(15, 10))
    
    # 能量曲线
    if 'energy' in data:
        ax1 = plt.subplot(2, 3, 1)
        energy = data['energy']
        ax1.plot(time, energy, 'b-', linewidth=1.5, label='Total Energy')
        if 'energy_T' in data:
            ax1.plot(time, data['energy_T'], 'r--', alpha=0.7, label='Kinetic')
        if 'energy_U' in data:
            ax1.plot(time, data['energy_U'], 'g--', alpha=0.7, label='Potential')
        ax1.set_ylabel('Energy [J]')
        ax1.set_xlabel('Time [s]')
        ax1.set_title('Energy Evolution')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 应用配置范围
        if cfg_energy.get('xlim'):
            ax1.set_xlim(cfg_energy['xlim'])
        if cfg_energy.get('ylim'):
            ax1.set_ylim(cfg_energy['ylim'])
    
    # 能量漂移
    if 'delta_energy' in data:
        ax2 = plt.subplot(2, 3, 2)
        de = data['delta_energy']
        ax2.plot(time, de, 'r-', linewidth=1)
        ax2.fill_between(time, de, alpha=0.3)
        ax2.set_ylabel('ΔE [J]')
        ax2.set_xlabel('Time [s]')
        ax2.set_title('Energy Drift')
        ax2.grid(True, alpha=0.3)
        
        # 应用配置范围
        if cfg_delta_e.get('xlim'):
            ax2.set_xlim(cfg_delta_e['xlim'])
        if cfg_delta_e.get('ylim'):
            ax2.set_ylim(cfg_delta_e['ylim'])
    
    # 末端位置
    if 'ee' in data:
        ax3 = plt.subplot(2, 3, 3)
        ee = data['ee']
        ax3.plot(time, ee[:, 0], 'r-', label='X', linewidth=1.5)
        ax3.plot(time, ee[:, 1], 'g-', label='Y', linewidth=1.5)
        ax3.plot(time, ee[:, 2], 'b-', label='Z', linewidth=1.5)
        ax3.set_ylabel('Position [m]')
        ax3.set_xlabel('Time [s]')
        ax3.set_title('End-Effector Position')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # 应用配置范围
        if cfg_ee_pos.get('xlim'):
            ax3.set_xlim(cfg_ee_pos['xlim'])
        if cfg_ee_pos.get('ylim'):
            ax3.set_ylim(cfg_ee_pos['ylim'])
    
    # 关节配置（显示前7列，即活跃DOF）
    if 'q' in data:
        ax4 = plt.subplot(2, 3, 4)
        q = data['q']
        n_dof = min(7, q.shape[1])  # 只显示前7个DOF（活跃关节）
        for i in range(n_dof):
            ax4.plot(time, q[:, i], label=f'q{i+1}', linewidth=1)
        ax4.set_ylabel('Joint Configuration [rad]')
        ax4.set_xlabel('Time [s]')
        ax4.set_title('Joint Configuration (Active DOF)')
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=8, ncol=2)
        
        # 应用配置范围
        if cfg_joints.get('xlim'):
            ax4.set_xlim(cfg_joints['xlim'])
        if cfg_joints.get('ylim'):
            ax4.set_ylim(cfg_joints['ylim'])
    
    # 末端速度（数值微分）
    if 'ee' in data:
        ax5 = plt.subplot(2, 3, 5)
        ee = data['ee']
        if len(time) > 1:
            dt = time[1] - time[0]
            ee_vel = np.linalg.norm(np.diff(ee, axis=0), axis=1) / dt
            ax5.plot(time[1:], ee_vel, 'purple', linewidth=1.5)
            ax5.set_ylabel('Speed [m/s]')
            ax5.set_xlabel('Time [s]')
            ax5.set_title('End-Effector Speed')
            ax5.grid(True, alpha=0.3)
            
            # 应用配置范围
            if cfg_ee_speed.get('xlim'):
                ax5.set_xlim(cfg_ee_speed['xlim'])
            if cfg_ee_speed.get('ylim'):
                ax5.set_ylim(cfg_ee_speed['ylim'])
    
    # 在3D中绘制末端轨迹
    if 'ee' in data:
        ax6 = plt.subplot(2, 3, 6, projection='3d')
        ee = data['ee']
        ax6.plot(ee[:, 0], ee[:, 1], ee[:, 2], 'b-', linewidth=1.5)
        ax6.scatter(ee[0, 0], ee[0, 1], ee[0, 2], c='g', s=100, marker='o', label='Start')
        ax6.scatter(ee[-1, 0], ee[-1, 1], ee[-1, 2], c='r', s=100, marker='s', label='End')
        ax6.set_xlabel('X [m]')
        ax6.set_ylabel('Y [m]')
        ax6.set_zlabel('Z [m]')
        ax6.set_title('End-Effector 3D Trajectory')
        ax6.legend()
        
        # 应用配置范围
        if cfg_traj3d.get('xlim'):
            ax6.set_xlim(cfg_traj3d['xlim'])
        if cfg_traj3d.get('ylim'):
            ax6.set_ylim(cfg_traj3d['ylim'])
        if cfg_traj3d.get('zlim'):
            ax6.set_zlim(cfg_traj3d['zlim'])
    
    plt.tight_layout()
    return fig

def main():
    parser = argparse.ArgumentParser(description='Analyze w10 VI Node simulation results')
    parser.add_argument('--path', required=True, help='Path to csv directory or parent directory containing subfolders')
    parser.add_argument('--plot', action='store_true', help='Show plots')
    parser.add_argument('--save-plot', help='Save plot to file (default: auto-save to fig dir)')
    parser.add_argument('--config', help='Path to plot configuration YAML file (default: auto-detect)')
    
    args = parser.parse_args()
    
    # 加载绘图配置
    config = load_plot_config(args.config)
    
    csv_path = Path(args.path)
    if not csv_path.exists():
        print(f"Error: Directory not found: {csv_path}")
        return 1
    
    # 检查是否为单个CSV目录（包含数据文件）或父目录（包含子文件夹）
    has_csv_files = any(csv_path.glob('*.csv'))
    subfolders = [d for d in csv_path.iterdir() if d.is_dir()]
    
    if has_csv_files and not subfolders:
        # 单个CSV目录模式
        print("Processing single CSV directory...")
        data = load_data(csv_path)
        if not data:
            print(f"Error: No CSV files found in {csv_path}")
            return 1
        print_summary(data, csv_path)
        fig = plot_results(data, config)
        _save_plot(fig, csv_path, args.save_plot, None)
        if args.plot:
            plt.show()
    elif subfolders:
        # 多子文件夹模式
        print(f"Processing parent directory with {len(subfolders)} subfolder(s)...")
        
        # 获取父目录名称
        parent_dir_name = csv_path.name
        print(f"Parent directory: {parent_dir_name}")
        
        success_count = 0
        for subfolder in sorted(subfolders):
            subfolder_name = subfolder.name
            print(f"\nProcessing subfolder: {subfolder_name}")
            
            data = load_data(subfolder)
            if not data:
                print(f"  Warning: No CSV files found in {subfolder}, skipping...")
                continue
            
            print_summary(data, subfolder, subfolder_name)
            fig = plot_results(data, config)
            _save_plot(fig, subfolder, args.save_plot, subfolder_name, parent_dir_name)
            
            if args.plot:
                plt.show()
            
            plt.close(fig)
            success_count += 1
        
        print(f"\n{'='*60}")
        print(f"Completed: {success_count}/{len(subfolders)} subfolders processed successfully")
        print(f"{'='*60}\n")
        
        if success_count == 0:
            return 1
    else:
        print(f"Error: {csv_path} is neither a CSV directory nor a parent directory")
        return 1
    
    return 0

def _save_plot(fig, csv_dir, custom_save_path, subfolder_name=None, parent_name=None):
    """保存绘图文件"""
    if custom_save_path:
        save_path = Path(custom_save_path)
    else:
        # 自动推断保存路径
        try:
            # 查找路径中的 w10_sim 目录
            parts = csv_dir.parts
            if 'w10_sim' in parts:
                w10_sim_idx = parts.index('w10_sim')
                # 构建 w10_sim/fig 路径
                fig_base_dir = Path(*parts[:w10_sim_idx+1]) / 'fig'
                
                # 如果有父目录名称，创建对应的子目录
                if parent_name:
                    fig_dir = fig_base_dir / parent_name
                else:
                    fig_dir = fig_base_dir
                
                fig_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成文件名
                if subfolder_name:
                    filename = f"w10_vi_{subfolder_name}_analysis.png"
                else:
                    filename = f"w10_vi_analysis.png"
                
                save_path = fig_dir / filename
            else:
                # 如果找不到 w10_sim 目录，则保存到 fig 子目录（相对路径）
                if parent_name:
                    fig_dir = csv_dir.parent.parent / 'fig' / parent_name
                else:
                    fig_dir = csv_dir.parent.parent / 'fig'
                fig_dir.mkdir(parents=True, exist_ok=True)
                
                if subfolder_name:
                    filename = f"w10_vi_{subfolder_name}_analysis.png"
                else:
                    filename = f"w10_vi_analysis.png"
                save_path = fig_dir / filename
        except Exception as e:
            print(f"Warning: Failed to auto-determine save path: {e}")
            if parent_name:
                fig_dir = Path('fig') / parent_name
            else:
                fig_dir = Path('fig')
            fig_dir.mkdir(parents=True, exist_ok=True)
            
            if subfolder_name:
                filename = f"w10_vi_{subfolder_name}_analysis.png"
            else:
                filename = f"w10_vi_analysis.png"
            save_path = fig_dir / filename
    
    # 保存图表
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {save_path}")

if __name__ == '__main__':
    sys.exit(main())
