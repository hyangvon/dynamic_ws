#!/usr/bin/env python3
"""
w10 VI Node 仿真结果分析脚本

用法：
    # 单个CSV目录
    python3 analyze_vi_results.py --path src/marvin_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/ctsvi_ad/
    
    # 多个子文件夹（会自动处理所有子文件夹）
    python3 analyze_vi_results.py --path src/marvin_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/
    
    # 显示图表
    python3 analyze_vi_results.py --path src/marvin_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/ --plot
    
    # 自定义配置文件
    python3 analyze_vi_results.py --path src/marvin_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/ --config config/plot_config.yaml
    
    # 自定义保存路径
    python3 analyze_vi_results.py --path src/marvin_sim/csv/q0p2_dt0p01_T10_a0p4_b0p04/ --save-plot /tmp/output.png

配置文件：
    - 默认配置文件位置: src/marvin_sim/config/plot_config.yaml
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
            Path('src/marvin_sim/config/plot_config.yaml'),
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
    
    # 加载系统总线动量 (centroidal)
    clm_file = csv_dir / 'centroidal_lin_momentum_history.csv'
    if clm_file.exists():
        data['centroidal_lin_momentum'] = np.loadtxt(clm_file, delimiter=',')
    
    # 加载力矩
    ft_file = csv_dir / 'force_torque_history.csv'
    if ft_file.exists():
        ft_raw = np.loadtxt(ft_file, delimiter=',')
        if ft_raw.ndim == 1:
            ft_raw = ft_raw.reshape(-1, 1)
        data['force_torque'] = ft_raw

    # 加载步长历史
    h_file = csv_dir / 'h_history.csv'
    if h_file.exists():
        data['h_history'] = np.loadtxt(h_file)

    # 加载能量灵敏度
    g_file = csv_dir / 'g_history.csv'
    if g_file.exists():
        data['g_history'] = np.loadtxt(g_file)
    gdagger_file = csv_dir / 'g_dagger_history.csv'
    if gdagger_file.exists():
        data['g_dagger_history'] = np.loadtxt(gdagger_file)
    dqk1_dhk_file = csv_dir / 'dqk1_dhk_norm_history.csv'
    if dqk1_dhk_file.exists():
        data['dqk1_dhk_norm_history'] = np.loadtxt(dqk1_dhk_file)

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
        print(f"\nEnergy Drift (overall):")
        print(f"  Max |ΔE|:           {np.max(np.abs(de)):>15.6f} J")
        print(f"  Relative Drift:     {np.max(np.abs(de))/np.max(np.abs(data['energy']))*100:>14.4f} %")

        # 施力后数值漂移：剔除外力做功引起的能量抬升
        force_off_idx = None
        if 'force_torque' in data:
            ft = data['force_torque']
            norms = np.linalg.norm(ft, axis=1)
            threshold = 1e-6 * (np.max(norms) if np.max(norms) > 0 else 1.0)
            active = norms > threshold
            if active.any():
                last_active = int(np.where(active)[0][-1])
                # 对齐 force_torque 与 delta_energy 长度（time_history 可能多一行）
                de_len = len(de)
                ft_len = len(ft)
                offset = de_len - ft_len  # ctsvi 初始步多一个能量点时 offset=1，否则=0
                force_off_idx = last_active + 1 + offset  # delta_energy 中施力后第一步
                force_off_idx = min(force_off_idx, de_len)

        if force_off_idx is not None and force_off_idx < len(de) - 1:
            post_de = de[force_off_idx:] - de[force_off_idx]  # 以施力结束时刻为新基准
            print(f"\nPost-force Numerical Drift (from force-off at step {force_off_idx}):")
            print(f"  Max |ΔE|:           {np.max(np.abs(post_de)):>15.6f} J")
            print(f"  Std Dev:            {np.std(post_de):>15.6f} J")
            print(f"  Relative Drift:     {np.max(np.abs(post_de))/np.max(np.abs(data['energy']))*100:>14.4f} %")
    
    if 'energy_T' in data and 'energy_U' in data:
        T = data['energy_T']
        U = data['energy_U']
        print(f"\nKinetic/Potential Energy:")
        print(f"  Peak Kinetic:       {np.max(T):>15.6f} J")
        print(f"  Peak Potential:     {np.max(U):>15.6f} J")
    
    if 'avg_runtime' in data:
        print(f"\nComputational Performance:")
        print(f"  Avg Step Time:      {data['avg_runtime']:>15.3f} ms")
    
    if 'g_history' in data:
        g = data['g_history']
        print(f"\nEnergy Sensitivity g_k:")
        print(f"  Max g_k:            {np.max(g):>15.6e}")
        print(f"  Min g_k:            {np.min(g):>15.6e}")
        print(f"  Std g_k:            {np.std(g):>15.6e}")
    if 'g_dagger_history' in data:
        gd = data['g_dagger_history']
        print(f"\nDamped Sensitivity g_k^\u2020:")
        print(f"  Max g_k^\u2020:      {np.max(gd):>15.6e}")
        print(f"  Min g_k^\u2020:      {np.min(gd):>15.6e}")
        print(f"  Std g_k^\u2020:      {np.std(gd):>15.6e}")
    
    if 'ee' in data:
        ee = data['ee']
        print(f"\nEnd-Effector Position:")
        print(f"  Initial: [{ee[0, 0]:.4f}, {ee[0, 1]:.4f}, {ee[0, 2]:.4f}]")
        print(f"  Final:   [{ee[-1, 0]:.4f}, {ee[-1, 1]:.4f}, {ee[-1, 2]:.4f}]")
        ee_dist = np.linalg.norm(ee[-1] - ee[0])
        print(f"  Total Displacement: {ee_dist:.4f} m")
    
    print(f"\n{'='*60}\n")


# ---------------------------------------------------------------------------
# 多积分器对比图（风格与 vi_compare_sim.py 保持一致）
# ---------------------------------------------------------------------------

_COMP_STYLE = {
    'ctsvi':   {'color': '#9467BD', 'linestyle': ':',  'linewidth': 2.0, 'label': 'CTSVI'},
    'atsvi':   {'color': '#000000', 'linestyle': '-',  'linewidth': 1.2, 'label': 'ATSVI'},
    'c_atsvi': {'color': '#D62728', 'linestyle': '-',  'linewidth': 2.0, 'label': 'C-ATSVI'},
}
_SUBFOLDER_ORDER = ['ctsvi', 'atsvi', 'c_atsvi']


def _init_comparison_style():
    """统一对比图字体与样式（与 vi_compare_sim.py 一致）"""
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'axes.titlesize': 20,
        'axes.titleweight': 'bold',
        'axes.labelsize': 18,
        'legend.fontsize': 18,
        'xtick.labelsize': 18,
        'ytick.labelsize': 18,
        'legend.frameon': True,
    })


def _save_comparison_fig(fig, parent_dir, plot_name):
    """将对比图保存到 fig/<parent_name>/comparison/ 目录"""
    parent_dir = Path(parent_dir)
    parts = parent_dir.parts
    if 'marvin_sim' in parts:
        idx = parts.index('marvin_sim')
        fig_base = Path(*parts[:idx + 1]) / 'fig'
    else:
        fig_base = parent_dir.parent / 'fig'
    fig_dir = fig_base / parent_dir.name / 'comparison'
    fig_dir.mkdir(parents=True, exist_ok=True)
    save_path = fig_dir / f"{plot_name}.png"
    fig.savefig(save_path, dpi=200)
    print(f"Comparison plot saved to: {save_path}")
    return save_path


def plot_comparison(all_data, parent_dir, config=None, show=False):
    """
    绘制多积分器对比图：能量漂移、时间步长、末端位置 Z 分量。
    风格与 vi_compare_sim.py 保持一致。

    参数：
        all_data: dict {subfolder_name: data_dict}
        parent_dir: Path，CSV 数据的父目录（用于推断保存路径）
        config: 绘图配置字典（xlim/ylim 等）
        show: 是否调用 plt.show()
    """
    # *** 重要：rcParams 必须在创建 figure 之前设置 ***
    _init_comparison_style()
    
    if not all_data:
        return
    if config is None:
        config = {}
    cfg_de = config.get('delta_energy', {}) or {}
    cfg_ee = config.get('end_effector_position', {}) or {}

    # 绘图顺序：预设顺序优先，其余按名称排序追加
    ordered = [k for k in _SUBFOLDER_ORDER if k in all_data]
    for k in sorted(all_data):
        if k not in ordered:
            ordered.append(k)

    def _style(name):
        return _COMP_STYLE.get(name, {
            'color': None, 'linestyle': '-', 'linewidth': 1.5, 'label': name
        })

    # ---- 1. 能量漂移对比 ----
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    plotted = False
    for name in ordered:
        d = all_data[name]
        if 'delta_energy' not in d or 'time' not in d:
            continue
        s = _style(name)
        ax1.plot(d['time'], d['delta_energy'],
                 label=f'ΔEnergy of {s["label"]}',
                 color=s['color'], linestyle=s['linestyle'], linewidth=s['linewidth'])
        plotted = True
    if plotted:
        ax1.ticklabel_format(style='sci', scilimits=(0, 0), axis='y', useMathText=True)
        ax1.set_xlabel('Time [s]')
        ax1.set_ylabel('Energy [J]')
        ax1.set_title('Energy Evolution')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim([0, 20])
        # ax1.set_xlim([0, 40])
        if cfg_de.get('ylim'):
            ax1.set_ylim(cfg_de['ylim'])
        # fig1.subplots_adjust(left=0.11, right=0.98, top=0.9, bottom=0.15)
        fig1.subplots_adjust(left=0.14, right=0.96, top=0.9, bottom=0.15)
        _save_comparison_fig(fig1, parent_dir, 'energy_comparison')
        if show:
            plt.show()
    plt.close(fig1)

    # ---- 2. 时间步长对比 ----
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    plotted = False
    for name in ordered:
        d = all_data[name]
        if 'h_history' not in d or 'time' not in d:
            continue
        s = _style(name)
        ax2.plot(d['time'], d['h_history'],
                 label=f'Time Step of {s["label"]}',
                 color=s['color'], linestyle=s['linestyle'], linewidth=s['linewidth'])
        plotted = True
    if plotted:
        ax2.ticklabel_format(style='sci', scilimits=(0, 0), axis='y', useMathText=True)
        ax2.set_xlabel('Time [s]')
        ax2.set_ylabel('Step [s]')
        ax2.set_title('Adaptive Time Step')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim([0, 20])
        # ax2.set_xlim([0, 40])
        # fig2.subplots_adjust(left=0.11, right=0.98, top=0.9, bottom=0.15)
        fig2.subplots_adjust(left=0.14, right=0.96, top=0.9, bottom=0.15)
        _save_comparison_fig(fig2, parent_dir, 'step_comparison')
        if show:
            plt.show()
    plt.close(fig2)

    # ---- 3. 末端位置 Z 分量对比 ----
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    plotted = False
    for name in ordered:
        d = all_data[name]
        if 'ee' not in d or 'time' not in d:
            continue
        ee = d['ee']
        if ee.ndim < 2 or ee.shape[1] < 3:
            continue
        s = _style(name)
        ax3.plot(d['time'], ee[:, 2],
                 label=f'Position Z of {s["label"]}',
                 color=s['color'], linestyle=s['linestyle'], linewidth=s['linewidth'])
        plotted = True
    if plotted:
        ax3.ticklabel_format(style='sci', scilimits=(0, 0), axis='y', useMathText=True)
        ax3.set_xlabel('Time [s]')
        ax3.set_ylabel('Position [m]')
        ax3.set_title('Tip Position')
        ax3.legend(loc='upper left')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim([0, 20])
        # ax3.set_xlim([0, 40])
        if cfg_ee.get('ylim'):
            ax3.set_ylim(cfg_ee['ylim'])
        # fig3.subplots_adjust(left=0.11, right=0.98, top=0.9, bottom=0.15)
        fig3.subplots_adjust(left=0.14, right=0.96, top=0.9, bottom=0.15)
        _save_comparison_fig(fig3, parent_dir, 'position_comparison')
        if show:
            plt.show()
    plt.close(fig3)

    # ---- 4. 系统总动量 Z 分量对比 ----
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    plotted = False
    for name in ordered:
        d = all_data[name]
        clm = d.get('centroidal_lin_momentum')
        if clm is None or 'time' not in d:
            continue
        if clm.ndim < 2 or clm.shape[1] < 3:
            continue
        s = _style(name)
        t = d['time'][:len(clm)]
        ax4.plot(t, clm[:, 2],
                 label=f'Momentum Z of {s["label"]}',
                 color=s['color'], linestyle=s['linestyle'], linewidth=s['linewidth'])
        plotted = True
    if plotted:
        ax4.ticklabel_format(style='sci', scilimits=(0, 0), axis='y', useMathText=True)
        ax4.set_xlabel('Time [s]')
        ax4.set_ylabel('Momentum [kg·m/s]')
        ax4.set_title('System Linear Momentum')
        ax4.legend(loc='upper left')
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim([0, 20])
        # ax4.set_xlim([0, 40])
        # fig4.subplots_adjust(left=0.11, right=0.98, top=0.9, bottom=0.15)
        fig4.subplots_adjust(left=0.14, right=0.96, top=0.9, bottom=0.15)
        _save_comparison_fig(fig4, parent_dir, 'momentum_z_comparison')
        if show:
            plt.show()
    plt.close(fig4)

    # ---- 5. 辛2-形式误差对比 ----
    fig5, ax5 = plt.subplots(figsize=(10, 5))
    plotted = False
    for name in ordered:
        d = all_data[name]
        if 'q' in d and 'momentum' in d:
            q = d['q']
            p = d['momentum']
            t = d['time'] if 'time' in d else np.arange(len(q))
            min_len = min(len(q), len(p))
            if min_len > 1:
                # 对齐长度
                q = q[:min_len]
                p = p[:min_len]
                dq = np.diff(q, axis=0)
                dp = np.diff(p, axis=0)
                omega = np.sum(dq * dp, axis=1)
                omega0 = omega[0]
                omega_err = np.abs(omega - omega0)
                s = _style(name)
                ax5.plot(t[1:min_len], omega_err, label=f'|Δω| of {s["label"]}', 
                        color=s['color'], linestyle=s['linestyle'], linewidth=s['linewidth'])
                plotted = True
    if plotted:
        ax5.ticklabel_format(style='sci', scilimits=(0, 0), axis='y', useMathText=True)
        ax5.set_xlabel('Time [s]')
        ax5.set_ylabel('Symplectic 2-form Error')
        ax5.set_title('Preservation Error of Symplectic 2-form')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        ax5.set_xlim([0, 20])
        # ax5.set_xlim([0, 40])
        # fig5.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.15)
        fig5.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)
        # fig5.subplots_adjust(left=0.14, right=0.96, top=0.9, bottom=0.15)
        _save_comparison_fig(fig5, parent_dir, 'symplectic2form_comparison')
        if show:
            plt.show()
    plt.close(fig5)

    # ---- 6. 能量灵敏度对比 ----
    fig6, ax6 = plt.subplots(figsize=(10, 5))
    plotted = False
    start_idx = 10
    for name in ordered:
        d = all_data[name]
        if 'time' not in d:
            continue
        t = d['time']
        s = _style(name)
        if 'g_history' in d:
            g = np.asarray(d['g_history'])
            if g.size <= start_idx:
                continue
            g = g[start_idx:]
            t_g = t
            if len(d['g_history']) == len(t) - 1:
                t_g = t[1:len(d['g_history'])+1]
            elif len(d['g_history']) != len(t):
                t_g = np.arange(len(d['g_history']))
            t_g = np.asarray(t_g)[start_idx:]
            ax6.plot(t_g, g, label=f'g_k of {s["label"]}',
                     color=s['color'], linestyle=s['linestyle'], linewidth=s['linewidth'])
            plotted = True
        if 'g_dagger_history' in d:
            gd = np.asarray(d['g_dagger_history'])
            if gd.size <= start_idx:
                continue
            gd = gd[start_idx:]
            t_gd = t
            if len(d['g_dagger_history']) == len(t) - 1:
                t_gd = t[1:len(d['g_dagger_history'])+1]
            elif len(d['g_dagger_history']) != len(t):
                t_gd = np.arange(len(d['g_dagger_history']))
            t_gd = np.asarray(t_gd)[start_idx:]
            ax6.plot(t_gd, gd, label=f'g_k^† of {s["label"]}',
                     color=s['color'], linestyle='--', linewidth=s['linewidth'])
            plotted = True
    if plotted:
        ax6.ticklabel_format(style='sci', scilimits=(0, 0), axis='y', useMathText=True)
        ax6.set_xlabel('Time [s]')
        ax6.set_ylabel('Sensitivity')
        ax6.set_title('Energy Sensitivity Comparison')
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        ax6.set_xlim([0, 20])
        # ax6.set_xlim([0, 40])
        fig6.subplots_adjust(left=0.14, right=0.96, top=0.9, bottom=0.15)
        _save_comparison_fig(fig6, parent_dir, 'sensitivity_comparison')
        if show:
            plt.show()
    plt.close(fig6)

    # ---- 7. 伪逆正则化函数 f(g) = g / (g^2 + eps) ----
    all_g_values = np.concatenate([d['g_history'] for d in all_data.values() if 'g_history' in d]) if any('g_history' in d for d in all_data.values()) else np.array([])
    if all_g_values.size > 0:
        eps = 1e-8
        g_range = np.linspace(-max(1.0, np.max(np.abs(all_g_values))) * 1.1,
                              max(1.0, np.max(np.abs(all_g_values))) * 1.1,
                              400)
        g_dagger_func = g_range / (g_range * g_range + eps)

        fig7, ax7 = plt.subplots(figsize=(10, 5))
        ax7.plot(g_range, g_dagger_func, 'k-', linewidth=1.5,
                 label=f'f(g)=g/(g^2+{eps:.0e})')

        for name in ordered:
            d = all_data[name]
            if 'g_history' in d and 'g_dagger_history' in d:
                s = _style(name)
                g = np.asarray(d['g_history'])
                gd = np.asarray(d['g_dagger_history'])
                if g.size > start_idx and gd.size > start_idx:
                    ax7.scatter(g[start_idx:], gd[start_idx:],
                                s=12, alpha=0.7,
                                color=s['color'], marker='o',
                                label=f"{s['label']} samples")

        ax7.set_xlabel('g_k')
        ax7.set_ylabel('g_k^†')
        ax7.set_title('Regularized Pseudoinverse Function f(g)=g/(g^2+ε)')
        ax7.grid(True, alpha=0.3)
        ax7.set_xlim([-5, 5])
        ax7.set_ylim([-100, 100])
        ax7.legend(loc='best', fontsize=8)
        fig7.subplots_adjust(left=0.14, right=0.96, top=0.9, bottom=0.15)
        _save_comparison_fig(fig7, parent_dir, 'g_regularization_function')
        if show:
            plt.show()
        plt.close(fig7)

    # ---- 8. C-ATSVI 步长灵敏度 ||∂q_{k+1}/∂h_k|| ----
    c_atsvi_name = None
    for name in ordered:
        if 'dqk1_dhk_norm_history' in all_data[name]:
            c_atsvi_name = name
            break

    if c_atsvi_name is not None:
        dq_norm = np.asarray(all_data[c_atsvi_name]['dqk1_dhk_norm_history'])
        t_dq = np.arange(len(dq_norm))

        fig8, ax8 = plt.subplots(figsize=(10, 5))
        ax8.plot(t_dq, dq_norm, '-', linewidth=1.5, color='tab:blue')
        ax8.set_xlabel('Step index k')
        ax8.set_ylabel(r"$\left\|\frac{\partial q_{k+1}}{\partial h_k}\right\|$")
        ax8.set_title(r"Implicit term of $e_k$")
        ax8.grid(True, alpha=0.3)
        ax8.set_xlim([0, 2000])
        # ax8.set_xlim([0, 4000])
        fig8.subplots_adjust(left=0.14, right=0.96, top=0.9, bottom=0.15)
        _save_comparison_fig(fig8, parent_dir, 'c_atsvi_dqk1_dhk_norm_history')
        if show:
            plt.show()
        plt.close(fig8)

def plot_results(data, config=None):
    """绘制仿真结果
    
    参数：
        data: 加载的仿真数据
        config: 绘图配置字典（来自plot_config.yaml）
    """
    if config is None:
        config = {}
    
    # 应用统一样式
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'axes.titlesize': 20,
        'axes.titleweight': 'bold',
        'axes.labelsize': 18,
        'legend.fontsize': 18,
        'xtick.labelsize': 18,
        'ytick.labelsize': 18,
        'legend.frameon': True,
    })
    
    time = data.get('time', np.arange(len(data.get('energy', []))))
    
    # 获取各项配置（如果不存在则为None，表示自动调整）
    cfg_energy = config.get('energy', {}) or {}
    cfg_delta_e = config.get('delta_energy', {}) or {}
    cfg_ee_pos = config.get('end_effector_position', {}) or {}
    cfg_ee_speed = config.get('end_effector_speed', {}) or {}
    cfg_joints = config.get('joint_configuration', {}) or {}
    cfg_traj3d = config.get('trajectory_3d', {}) or {}
    cfg_momentum = config.get('momentum', {}) or {}
    
    fig = plt.figure(figsize=(18, 16))
    
    # 能量曲线
    if 'energy' in data:
        ax1 = plt.subplot(4, 3, 1)
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
        ax2 = plt.subplot(4, 3, 2)
        de = data['delta_energy']
        ax2.plot(time, de, 'r-', linewidth=1, label='ΔE (from t=0)')
        ax2.fill_between(time, de, alpha=0.2, color='red')

        # 叠加施力后数值漂移曲线（以施力结束时刻为新零点）
        force_off_idx = None
        if 'force_torque' in data:
            ft = data['force_torque']
            norms = np.linalg.norm(ft, axis=1)
            threshold = 1e-6 * (np.max(norms) if np.max(norms) > 0 else 1.0)
            active = norms > threshold
            if active.any():
                last_active = int(np.where(active)[0][-1])
                offset = len(de) - len(ft)
                force_off_idx = min(last_active + 1 + offset, len(de))
        if force_off_idx is not None and force_off_idx < len(de) - 1:
            post_t = time[force_off_idx:]
            post_de = de[force_off_idx:] - de[force_off_idx]
            ax2.plot(post_t, post_de, 'b-', linewidth=1.5,
                     label='Post-force ΔE (re-zeroed)')
            ax2.axvline(x=time[force_off_idx], color='gray', linestyle='--',
                        linewidth=1, alpha=0.7, label='Force off')
            ax2.legend(fontsize=7)

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
        ax3 = plt.subplot(3, 3, 3)
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
        ax4 = plt.subplot(3, 3, 4)
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
        ax5 = plt.subplot(3, 3, 5)
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
        ax6 = plt.subplot(3, 3, 6, projection='3d')
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
    
    # 系统总线动量 XYZ 分量
    if 'centroidal_lin_momentum' in data:
        ax7 = plt.subplot(3, 3, 7)
        clm = data['centroidal_lin_momentum']
        t_clm = time[:len(clm)]
        ax7.plot(t_clm, clm[:, 0], 'r-', label='px', linewidth=1.5)
        ax7.plot(t_clm, clm[:, 1], 'g-', label='py', linewidth=1.5)
        ax7.plot(t_clm, clm[:, 2], 'b-', label='pz', linewidth=1.5)
        ax7.set_ylabel('Linear Momentum [kg·m/s]')
        ax7.set_xlabel('Time [s]')
        ax7.set_title('System Total Linear Momentum')
        ax7.grid(True, alpha=0.3)
        ax7.legend(fontsize=9)
        if cfg_momentum.get('xlim'):
            ax7.set_xlim(cfg_momentum['xlim'])
        if cfg_momentum.get('ylim'):
            ax7.set_ylim(cfg_momentum['ylim'])
    elif 'momentum' in data:
        # 备用：旧数据依然画关节广义动量
        ax7 = plt.subplot(3, 3, 7)
        p = data['momentum']
        n_dof = min(7, p.shape[1])
        for i in range(n_dof):
            ax7.plot(time[:len(p)], p[:, i], label=f'p{i+1}', linewidth=1)
        ax7.set_ylabel('Generalized Momentum [kg·m²/s]')
        ax7.set_xlabel('Time [s]')
        ax7.set_title('Generalized Momentum (joint space)')
        ax7.grid(True, alpha=0.3)
        ax7.legend(fontsize=8, ncol=2)
        if cfg_momentum.get('xlim'):
            ax7.set_xlim(cfg_momentum['xlim'])
        if cfg_momentum.get('ylim'):
            ax7.set_ylim(cfg_momentum['ylim'])

    # --------- 新增：辛2-形式误差 ---------
    if 'q' in data and 'momentum' in data:
        q = data['q']
        p = data['momentum']
        if len(q) > 1 and len(p) > 1 and len(q) == len(p):
            dq = np.diff(q, axis=0)
            dp = np.diff(p, axis=0)
            # 对每一步，omega_n = sum_i dq_i * dp_i
            omega = np.sum(dq * dp, axis=1)
            omega0 = omega[0]
            omega_err = np.abs(omega - omega0)
            ax8 = plt.subplot(3, 3, 8)
            ax8.plot(time[1:], omega_err, 'm-', linewidth=1.5, label='|Δω|')
            ax8.set_ylabel('Symplectic 2-form Error')
            ax8.set_xlabel('Time [s]')
            ax8.set_title('Preservation Error of Symplectic 2-form')
            ax8.grid(True, alpha=0.3)
            ax8.legend()

    plt.tight_layout()
    return fig

def main():
    parser = argparse.ArgumentParser(description='Analyze marvin VI Node simulation results')
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
        
        all_data = {}
        success_count = 0
        for subfolder in sorted(subfolders):
            subfolder_name = subfolder.name
            print(f"\nProcessing subfolder: {subfolder_name}")
            
            data = load_data(subfolder)
            if not data:
                print(f"  Warning: No CSV files found in {subfolder}, skipping...")
                continue
            
            all_data[subfolder_name] = data
            print_summary(data, subfolder, subfolder_name)
            fig = plot_results(data, config)
            _save_plot(fig, subfolder, args.save_plot, subfolder_name, parent_dir_name)
            
            if args.plot:
                plt.show()
            
            plt.close(fig)
            success_count += 1

        # 绘制多积分器对比图
        if all_data:
            print(f"\nGenerating comparison plots...")
            plot_comparison(all_data, csv_path, config, show=args.plot)

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
            # 查找路径中的 w10_force_sim 目录
            parts = csv_dir.parts
            if 'marvin_sim' in parts:
                w10_sim_idx = parts.index('marvin_sim')
                # 构建 w10_force_sim/fig 路径
                fig_base_dir = Path(*parts[:w10_sim_idx+1]) / 'fig'
                
                # 如果有父目录名称，创建对应的子目录
                if parent_name:
                    fig_dir = fig_base_dir / parent_name
                else:
                    fig_dir = fig_base_dir
                
                fig_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成文件名
                if subfolder_name:
                    filename = f"{subfolder_name}_analysis.png"
                else:
                    filename = f"analysis.png"
                
                save_path = fig_dir / filename
            else:
                # 如果找不到 w10_force_sim 目录，则保存到 fig 子目录（相对路径）
                if parent_name:
                    fig_dir = csv_dir.parent.parent / 'fig' / parent_name
                else:
                    fig_dir = csv_dir.parent.parent / 'fig'
                fig_dir.mkdir(parents=True, exist_ok=True)
                
                if subfolder_name:
                    filename = f"vi_{subfolder_name}_analysis.png"
                else:
                    filename = f"vi_analysis.png"
                save_path = fig_dir / filename
        except Exception as e:
            print(f"Warning: Failed to auto-determine save path: {e}")
            if parent_name:
                fig_dir = Path('fig') / parent_name
            else:
                fig_dir = Path('fig')
            fig_dir.mkdir(parents=True, exist_ok=True)
            
            if subfolder_name:
                filename = f"vi_{subfolder_name}_analysis.png"
            else:
                filename = f"vi_analysis.png"
            save_path = fig_dir / filename
    
    # 保存图表
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"Plot saved to: {save_path}")

if __name__ == '__main__':
    sys.exit(main())
