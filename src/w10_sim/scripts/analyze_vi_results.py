#!/usr/bin/env python3
"""
w10 VI Node 仿真结果分析脚本

用法:
    python3 analyze_vi_results.py --path src/w10_sim/csv/w10_dt0.001_T3.0/vi_ad/
    python3 analyze_vi_results.py --path src/w10_sim/csv/w10_dt0.001_T3.0/vi_ad/ --plot
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import sys

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

def print_summary(data, csv_dir):
    """打印仿真统计信息"""
    print(f"\n{'='*60}")
    print(f"Simulation Results Summary")
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

def plot_results(data):
    """绘制仿真结果"""
    time = data.get('time', np.arange(len(data.get('energy', []))))
    
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
    
    plt.tight_layout()
    return fig

def main():
    parser = argparse.ArgumentParser(description='Analyze w10 VI Node simulation results')
    parser.add_argument('--path', required=True, help='Path to csv directory')
    parser.add_argument('--plot', action='store_true', help='Show plots')
    parser.add_argument('--save-plot', help='Save plot to file (default: auto-save to fig dir)')
    
    args = parser.parse_args()
    
    csv_dir = Path(args.path)
    if not csv_dir.exists():
        print(f"Error: Directory not found: {csv_dir}")
        return 1
    
    # 加载数据
    data = load_data(csv_dir)
    
    if not data:
        print(f"Error: No CSV files found in {csv_dir}")
        return 1
    
    # 打印总结
    print_summary(data, csv_dir)
    
    # 绘制图表
    fig = plot_results(data)
    
    # 确定保存路径
    if args.save_plot:
        save_path = Path(args.save_plot)
    else:
        # 自动推断保存路径：从 csv_dir 中找到 w10_sim 目录，然后保存到 fig 子目录
        try:
            # 查找路径中的 w10_sim 目录
            parts = csv_dir.parts
            if 'w10_sim' in parts:
                w10_sim_idx = parts.index('w10_sim')
                # 构建 w10_sim/fig 路径
                fig_dir = Path(*parts[:w10_sim_idx+1]) / 'fig'
                fig_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成文件名
                timestamp = ''
                if 'time_history.csv' in [f.name for f in csv_dir.glob('*')]:
                    # 从 csv_dir 名称生成文件名
                    time_file = csv_dir / 'time_history.csv'
                    time_data = np.loadtxt(time_file)
                    duration = f"T{time_data[-1]:.2g}".replace('.', 'p')
                    dt = f"dt{time_data[1]-time_data[0]:.2g}".replace('.', 'p') if len(time_data) > 1 else "dt_unknown"
                    timestamp = f"_{dt}_{duration}"
                
                save_path = fig_dir / f"w10_vi_analysis{timestamp}.png"
            else:
                # 如果找不到 w10_sim 目录，则保存到 fig 子目录（相对路径）
                fig_dir = csv_dir.parent.parent / 'fig'
                fig_dir.mkdir(parents=True, exist_ok=True)
                save_path = fig_dir / 'w10_vi_analysis.png'
        except Exception as e:
            print(f"Warning: Failed to auto-determine save path: {e}")
            fig_dir = Path('fig')
            fig_dir.mkdir(parents=True, exist_ok=True)
            save_path = fig_dir / 'w10_vi_analysis.png'
    
    # 保存图表
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Plot automatically saved to: {save_path}")
    
    # 显示图表（如果指定了 --plot）
    if args.plot:
        plt.show()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
