#!/usr/bin/env python3
"""
c_atsvi Lyapunov 增益自动整定脚本

遍历 alpha ∈ [0, 1.0] (步长 0.05) 和 beta ∈ [0, 0.5] (步长 0.01)，
找到 Relative Energy Drift 最小的参数组合。

用法（从 dynamic_ws 目录运行）：
    source install/setup.bash

    # 全量扫描（使用 yaml 中的 duration，耗时较长）：
    python3 src/marvin_sim/scripts/tune_c_atsvi.py

    # 快速预筛（建议先用短 duration 定位区域）：
    python3 src/marvin_sim/scripts/tune_c_atsvi.py --sweep-duration 5.0

    # 断点续跑（自动跳过已有结果）：
    python3 src/marvin_sim/scripts/tune_c_atsvi.py --resume

    # 仅重新绘制已有扫描结果的热力图：
    python3 src/marvin_sim/scripts/tune_c_atsvi.py \\
        --plot-only src/marvin_sim/sweep_results/sweep_20260416_123456.csv

文件结构（不覆盖已有内容）：
    src/marvin_sim/csv/<label>/c_atsvi/  —— 每次仿真原始 CSV（与手动运行完全一致）
    src/marvin_sim/sweep_results/
        sweep_<timestamp>.csv            —— 扫描汇总表（alpha, beta, drift）
        best_params_<timestamp>.json     —— 最优参数
        heatmap_<timestamp>.png          —— 热力图
"""

import subprocess
import numpy as np
import csv
import json
import time
import sys
import argparse
import yaml
import itertools
import shutil
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def fmt_double_label(v: float) -> str:
    """
    与 C++ c_atsvi_node 中 fmt_double_label() 完全一致，
    确保 Python 预测的路径名与节点实际输出路径匹配。
    """
    s = f"{v:.6f}"
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    s = s.replace('.', 'p')
    return s


def get_csv_dir(q_init_0: float, dt: float, dur: float,
                alpha: float, beta: float) -> Path:
    """根据参数构造节点输出的 CSV 目录路径。"""
    label = (f"q{fmt_double_label(q_init_0)}"
             f"_dt{fmt_double_label(dt)}"
             f"_T{fmt_double_label(dur)}"
             f"_a{fmt_double_label(alpha)}"
             f"_b{fmt_double_label(beta)}")
    return Path(f"src/marvin_sim/csv/{label}/c_atsvi")


def compute_drift_metrics(csv_dir: Path) -> tuple[float | None, float | None]:
    """
    计算施力后能量漂移指标，与 analyze_vi_results.py 的 Post-force Numerical Drift 逻辑一致。
    返回 (max_drift%, std_dev%) 两个指标，失败时返回 (None, None)。
    """
    energy_file = csv_dir / "energy_history.csv"
    if not energy_file.exists():
        return None, None
    try:
        energy = np.loadtxt(energy_file)
        if energy.ndim == 0 or len(energy) < 2:
            return None, None
        de = energy - energy[0]
        max_e = np.max(np.abs(energy))
        if max_e < 1e-15:
            return None, None

        # --- 施力后数值漂移（与 analyze_vi_results.py 相同逻辑）---
        ft_file = csv_dir / "force_torque_history.csv"
        force_off_idx = None
        if ft_file.exists():
            ft_raw = np.loadtxt(ft_file, delimiter=',')
            if ft_raw.ndim == 1:
                ft_raw = ft_raw.reshape(-1, 1)
            norms = np.linalg.norm(ft_raw, axis=1)
            threshold = 1e-6 * (np.max(norms) if np.max(norms) > 0 else 1.0)
            active = norms > threshold
            if active.any():
                last_active = int(np.where(active)[0][-1])
                offset = len(de) - len(ft_raw)
                force_off_idx = min(last_active + 1 + offset, len(de))

        if force_off_idx is not None and force_off_idx < len(de) - 1:
            post_de = de[force_off_idx:] - de[force_off_idx]
        else:
            post_de = de

        max_drift = float(np.max(np.abs(post_de)) / max_e * 100.0)
        std_dev   = float(np.std(post_de) / max_e * 100.0)
        return max_drift, std_dev
    except Exception:
        return None, None


def compute_relative_drift(csv_dir: Path) -> float | None:
    """向后兼容包装，返回 max_drift%。"""
    drift, _ = compute_drift_metrics(csv_dir)
    return drift


def run_simulation(alpha: float, beta: float,
                   params_file: str,
                   sweep_duration: float | None,
                   timeout: int,
                   cwd: str) -> bool:
    """
    调用 ros2 run 运行 c_atsvi_node。
    因为节点使用 automatically_declare_parameters_from_overrides，
    命令行 -p 的顺序无法保证覆盖 yaml 文件中的同名参数，
    所以将 alpha/beta/duration 写入临时 yaml 副本，再让节点加载该副本。
    临时文件用完即删。
    """
    import tempfile, copy

    # 读取原始 yaml
    with open(params_file) as f:
        raw = yaml.safe_load(f)

    # 修改 c_atsvi_node 节中的增益；如果节不存在则创建
    node_sec = raw.setdefault('c_atsvi_node', {})
    ros_params = node_sec.setdefault('ros__parameters', {})
    ros_params['lyap_alpha'] = float(alpha)
    ros_params['lyap_beta']  = float(beta)

    # 同时覆盖 /** 段中的 duration（如需）
    if sweep_duration is not None:
        raw.setdefault('/**', {}).setdefault('ros__parameters', {})['duration'] = float(sweep_duration)

    # 写临时文件
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', delete=False, dir='/tmp'
    )
    yaml.dump(raw, tmp, default_flow_style=False, allow_unicode=True)
    tmp.close()
    tmp_path = tmp.name

    try:
        cmd = [
            "ros2", "run", "marvin_sim", "c_atsvi_node",
            "--ros-args",
            "--params-file", tmp_path,
        ]
        result = subprocess.run(
            cmd,
            cwd=cwd,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] alpha={alpha:.4f} beta={beta:.4f}", flush=True)
        return False
    except Exception as e:
        print(f"  [ERROR] {e}", flush=True)
        return False
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def fmt_eta(n_total_run: int, n_done_run: int, elapsed_s: float) -> str:
    if n_done_run == 0:
        return "??"
    avg = elapsed_s / n_done_run
    remaining = avg * (n_total_run - n_done_run)
    h, rem = divmod(int(remaining), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}h{m:02d}m{s:02d}s"


def find_ctsvi_ref_dir(q_init_0: float, dt_base: float,
                       base_dir: Path = Path('src/marvin_sim/csv')) -> Path | None:
    """在已有 CSV 目录中查找与当前参数匹配的 ctsvi 参考数据目录。"""
    q_label  = fmt_double_label(q_init_0)
    dt_label = fmt_double_label(dt_base)
    prefix   = f"q{q_label}_dt{dt_label}_T"
    for parent in sorted(base_dir.glob(f"{prefix}*")):
        candidate = parent / 'ctsvi'
        if (candidate / 'energy_history.csv').exists():
            return candidate
    return None


# ---------------------------------------------------------------------------
# 热力图
# ---------------------------------------------------------------------------

def plot_heatmap(alphas: np.ndarray, betas: np.ndarray,
                 results: dict, output_dir: Path, tag: str,
                 std_results: dict | None = None,
                 ref_std: float | None = None) -> Path | None:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
    except ImportError:
        print("警告: matplotlib 未安装，跳过热力图绘制")
        return None

    # 与对比图保持一致的全局样式
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'axes.titlesize': 20,
        'axes.titleweight': 'bold',
        'axes.labelsize': 18,
        'legend.fontsize': 14,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.frameon': True,
    })

    a_step = float(alphas[1] - alphas[0]) if len(alphas) > 1 else 0.05
    b_step = float(betas[1]  - betas[0])  if len(betas)  > 1 else 0.01
    extent = [betas[0]  - b_step * 0.5, betas[-1]  + b_step * 0.5,
              alphas[0] - a_step * 0.5, alphas[-1] + a_step * 0.5]

    def _build_grid(data: dict) -> np.ndarray:
        Z = np.full((len(alphas), len(betas)), np.nan)
        for i, a in enumerate(alphas):
            for j, b in enumerate(betas):
                key = (round(float(a), 6), round(float(b), 6))
                if key in data:
                    Z[i, j] = data[key]
        return Z

    Z_drift = _build_grid(results)
    Z_std   = _build_grid(std_results) if std_results else None

    # # --- 子图 1：Max Drift 对数色阶 ---
    # n_cols = 2 if Z_std is not None else 1
    # fig, axes = plt.subplots(1, n_cols, figsize=(9 * n_cols, 7))
    # if n_cols == 1:
    #     axes = [axes]
    # ax1 = axes[0]
    # valid1 = Z_drift[~np.isnan(Z_drift)]
    # norm1 = (mcolors.LogNorm(vmin=max(valid1.min(), 1e-12), vmax=valid1.max())
    #          if len(valid1) > 0 and valid1.min() > 0 else None)
    # im1 = ax1.imshow(Z_drift, aspect='auto', origin='lower', norm=norm1,
    #                  extent=extent, cmap='RdYlGn_r')
    # plt.colorbar(im1, ax=ax1, label='Max Drift [%] (log)')
    # ax1.set_xlabel('beta')
    # ax1.set_ylabel('alpha')
    # ax1.set_title('Max Relative Energy Drift [%] (log scale)')

    # --- 单图：Std Dev 对数色阶 ---
    fig, ax2 = plt.subplots(1, 1, figsize=(9, 7))
    norm2 = None
    if Z_std is not None:
        valid2 = Z_std[~np.isnan(Z_std)]
        norm2 = (mcolors.LogNorm(vmin=max(valid2.min(), 1e-12), vmax=valid2.max())
                 if len(valid2) > 0 and valid2.min() > 0 else None)
        im2 = ax2.imshow(Z_std, aspect='auto', origin='lower', norm=norm2,
                         extent=extent, cmap='RdYlGn_r')
        cbar2 = plt.colorbar(im2, ax=ax2, label='Std Dev [%] (log)')
        cbar2.ax.tick_params(labelsize=14)
        cbar2.set_label('Std Dev [%] (log)', fontsize=16)
        ax2.set_xlabel('beta')
        ax2.set_ylabel('alpha')
        ax2.set_title('C-ATSVI Energy Drift Std Dev [%] (log scale)')
        # # --- 在 colorbar 上标出 CTSVI 参考标记 ---
        # if ref_std is not None and norm2 is not None:
        #     try:
        #         y_pos = float(norm2(ref_std))
        #         if 0.0 <= y_pos <= 1.0:
        #             cbar2.ax.scatter(0.5, y_pos, marker='*', s=300,
        #                              color='black', zorder=5,
        #                              transform=cbar2.ax.transAxes)
        #             cbar2.ax.text(-0.05, y_pos, f'CTSVI\n{ref_std:.2e}%',
        #                           transform=cbar2.ax.transAxes, color='black',
        #                           fontsize=14, fontweight='bold',
        #                           va='center', ha='right',
        #                           bbox=dict(boxstyle='round,pad=0.2',
        #                                     facecolor='white', alpha=0.6,
        #                                     edgecolor='none'))
        #     except Exception:
        #         pass
        # --- 叠加 std(C-ATSVI) = std(CTSVI) 的等值线 ---
        if ref_std is not None and ref_std > 0:
            try:
                cs = ax2.contour(Z_std, levels=[ref_std], colors='black',
                                 linewidths=1.5, linestyles='--', origin='lower',
                                 extent=extent)
                ax2.clabel(cs, fmt={ref_std: 'C-ATSVI = CTSVI'}, fontsize=14,
                           inline=True)
            except Exception:
                pass

    fig.suptitle('C-ATSVI Lyapunov Gain Sweep — Relative Energy Drift', fontsize=22, fontweight='bold')
    plt.tight_layout()

    save_path = output_dir / f"heatmap_{tag}.png"
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"热力图已保存至: {save_path}")
    return save_path


# ---------------------------------------------------------------------------
# 从 CSV 结果文件重建 results dict（用于 --plot-only）
# ---------------------------------------------------------------------------

def load_results_csv(results_csv: Path) -> tuple[dict, dict, np.ndarray, np.ndarray]:
    results = {}
    std_results = {}
    with open(results_csv, newline='') as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            try:
                a = round(float(row['alpha']), 6)
                b = round(float(row['beta']), 6)
                d_str = row.get('relative_drift_%', '')
                if d_str and d_str not in ('FAILED', ''):
                    results[(a, b)] = float(d_str)
                s_str = row.get('std_dev_%', '')
                if s_str and s_str not in ('FAILED', ''):
                    std_results[(a, b)] = float(s_str)
            except (ValueError, KeyError):
                pass

    if not results:
        return results, std_results, np.array([]), np.array([])

    alphas = sorted(set(k[0] for k in results))
    betas  = sorted(set(k[1] for k in results))
    return results, std_results, np.array(alphas), np.array(betas)


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description='c_atsvi Lyapunov 增益自动整定',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--sweep-duration', type=float, default=None,
                        help='每次仿真时长（覆盖 yaml 中的 duration）。'
                             '建议先用 5.0 快速预筛，确认最优区域后再全量扫描。')
    parser.add_argument('--alpha-start', type=float, default=0.0)
    parser.add_argument('--alpha-end',   type=float, default=1.0)
    parser.add_argument('--alpha-step',  type=float, default=0.05)
    parser.add_argument('--beta-start',  type=float, default=0.0)
    parser.add_argument('--beta-end',    type=float, default=0.5)
    parser.add_argument('--beta-step',   type=float, default=0.01)
    parser.add_argument('--resume',      action='store_true', default=True,
                        help='跳过已有 energy_history.csv 的参数组合（默认开启）')
    parser.add_argument('--no-resume',   dest='resume', action='store_false',
                        help='强制重新运行所有组合')
    parser.add_argument('--plot',        action='store_true', default=False,
                        help='扫描完成后显示热力图')
    parser.add_argument('--plot-only',   type=str, default=None, metavar='CSV',
                        help='不运行仿真，仅根据已有汇总 CSV 生成热力图并退出')
    parser.add_argument('--timeout',     type=int, default=600,
                        help='每次仿真超时时间（秒，默认 600）')
    parser.add_argument('--params-file', type=str, default=None,
                        help='yaml 配置文件路径（默认自动查找）')
    parser.add_argument('--output-dir',  type=str,
                        default='src/marvin_sim/sweep_results',
                        help='扫描结果保存目录（默认 src/marvin_sim/sweep_results/）')
    parser.add_argument('--ref-dir',     type=str, default=None,
                        help='CTSVI CSV 目录路径，用于在热力图 colorbar 上标记参考标准差（不指定则自动查找）')

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # --plot-only 模式：只重绘热力图
    # ------------------------------------------------------------------
    if args.plot_only:
        results_csv = Path(args.plot_only)
        if not results_csv.exists():
            print(f"ERROR: 找不到结果文件 {results_csv}", file=sys.stderr)
            return 1
        results, std_results, alphas, betas = load_results_csv(results_csv)
        if not results:
            print("ERROR: 结果文件为空或格式错误", file=sys.stderr)
            return 1
        tag = results_csv.stem
        output_dir = results_csv.parent
        best_key = min(results, key=results.get)
        print(f"\n从 {results_csv} 加载了 {len(results)} 条结果")
        print(f"最优参数: alpha={best_key[0]:.4f}  beta={best_key[1]:.4f}"
              f"  drift={results[best_key]:.6e} %")
        ref_std = None
        if args.ref_dir:
            _, ref_std = compute_drift_metrics(Path(args.ref_dir))
        plot_heatmap(alphas, betas, results, output_dir, tag,
                     std_results=std_results or None, ref_std=ref_std)
        if args.plot:
            import matplotlib.pyplot as plt
            plt.show()
        return 0

    # ------------------------------------------------------------------
    # 查找 yaml 文件
    # ------------------------------------------------------------------
    if args.params_file:
        params_file = Path(args.params_file)
    else:
        candidates = [
            Path('src/marvin_sim/config/vi_params.yaml'),
            Path('config/vi_params.yaml'),
        ]
        params_file = next((p for p in candidates if p.exists()), None)
        if params_file is None:
            print("ERROR: 找不到 vi_params.yaml，请通过 --params-file 指定",
                  file=sys.stderr)
            return 1

    if not params_file.exists():
        print(f"ERROR: 找不到配置文件 {params_file}", file=sys.stderr)
        return 1

    params_file = params_file.resolve()  # 转为绝对路径，避免 cwd 切换时失效
    print(f"使用配置文件: {params_file}")

    # ------------------------------------------------------------------
    # 确定工作目录（dynamic_ws 根目录）
    # 节点用相对路径写 CSV，必须在 dynamic_ws 下运行才能找到
    # ------------------------------------------------------------------
    cwd = str(Path.cwd().resolve())
    # 如果当前不在 dynamic_ws 下，尝试向上查找
    p = Path(cwd)
    while p != p.parent:
        if (p / 'src').is_dir() and (p / 'install').is_dir():
            cwd = str(p)
            break
        p = p.parent
    print(f"节点工作目录 (cwd): {cwd}")

    # ------------------------------------------------------------------
    # 读取 yaml 基础参数（用于推断输出路径）
    # ------------------------------------------------------------------
    with open(params_file) as f:
        raw_yaml = yaml.safe_load(f)

    ros_params = raw_yaml.get('/**', {}).get('ros__parameters', {})
    q_init_vec = ros_params.get('q_init', [0.0])
    q_init_0   = float(q_init_vec[0]) if q_init_vec else 0.0
    dt_base    = float(ros_params.get('timestep', 0.01))
    dur_base   = float(ros_params.get('duration', 30.0))
    dur_actual = args.sweep_duration if args.sweep_duration is not None else dur_base

    print(f"q_init[0]={q_init_0:.6f}  dt={dt_base}  sweep_duration={dur_actual}")

    # 查找 CTSVI 参考标准差（用于热力图 colorbar 标注）
    ref_std = None
    _ref_csv = Path(args.ref_dir) if args.ref_dir else find_ctsvi_ref_dir(q_init_0, dt_base)
    if _ref_csv is not None:
        _, ref_std = compute_drift_metrics(_ref_csv)
        if ref_std is not None:
            print(f"CTSVI 参考标准差: {ref_std:.6e}%  (from {_ref_csv})")

    # ------------------------------------------------------------------
    # 生成参数网格
    # ------------------------------------------------------------------
    # 用 round 消除浮点累积误差
    alphas = np.round(
        np.arange(args.alpha_start,
                  args.alpha_end + args.alpha_step * 0.5,
                  args.alpha_step), 6)
    betas = np.round(
        np.arange(args.beta_start,
                  args.beta_end + args.beta_step * 0.5,
                  args.beta_step), 6)
    combos = list(itertools.product(alphas, betas))
    n_total = len(combos)

    print(f"\n参数网格: alpha {len(alphas)} 个 × beta {len(betas)} 个 = {n_total} 组合")
    print(f"预计时长（仅供参考）：每次仿真约 {dur_actual:.0f}s 壁钟时间 × {n_total} ="
          f" ~{dur_actual * n_total / 3600:.1f} 小时（可用 --sweep-duration 缩短）\n")

    # ------------------------------------------------------------------
    # 创建输出目录
    # ------------------------------------------------------------------
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_csv_path = output_dir / f"sweep_{timestamp}.csv"

    # ------------------------------------------------------------------
    # 扫描主循环
    # ------------------------------------------------------------------
    all_results: dict[tuple, float] = {}      # (alpha, beta) -> max_drift %
    all_std_results: dict[tuple, float] = {}  # (alpha, beta) -> std_dev %
    best = {'alpha': None, 'beta': None, 'drift': float('inf')}

    n_skipped = 0   # 因 resume 跳过的数量
    n_run     = 0   # 实际运行的数量
    t_run_start = time.time()  # 仅统计实际运行的耗时

    with open(results_csv_path, 'w', newline='') as results_fp:
        writer = csv.writer(results_fp)
        writer.writerow(['alpha', 'beta', 'relative_drift_%', 'std_dev_%', 'wall_time_s', 'status'])
        results_fp.flush()

        def _write_row(a, b, drift_val, std_val, wall_t, status):
            drift_str = f"{drift_val:.10f}" if drift_val is not None else 'FAILED'
            std_str   = f"{std_val:.10f}"   if std_val   is not None else 'FAILED'
            writer.writerow([f"{a}", f"{b}", drift_str, std_str, f"{wall_t:.1f}", status])
            results_fp.flush()

        def _update_best(a, b, drift):
            nonlocal best
            if drift is not None and drift < best['drift']:
                best = {'alpha': a, 'beta': b, 'drift': drift}

        for idx, (alpha, beta) in enumerate(combos):
            key = (round(float(alpha), 6), round(float(beta), 6))
            csv_dir = get_csv_dir(q_init_0, dt_base, dur_actual, alpha, beta)

            # ---- resume：已有 energy_history.csv，直接读取 ----
            if args.resume and (csv_dir / 'energy_history.csv').exists():
                drift, std = compute_drift_metrics(csv_dir)
                if drift is not None:
                    all_results[key] = drift
                    if std is not None:
                        all_std_results[key] = std
                    _write_row(alpha, beta, drift, std, 0.0, 'resume_from_csv')
                    _update_best(alpha, beta, drift)
                    n_skipped += 1
                    continue
                # 文件存在但读取失败，继续正常运行

            # ---- 运行仿真 ----
            elapsed_run = time.time() - t_run_start
            eta = fmt_eta(n_total - n_skipped, n_run, elapsed_run)
            print(f"[{idx+1:5d}/{n_total}] alpha={alpha:.4f} beta={beta:.4f}  "
                  f"已运行={n_run}  已跳过={n_skipped}  ETA={eta}",
                  flush=True)

            t0 = time.time()
            success = run_simulation(
                alpha, beta, str(params_file), args.sweep_duration, args.timeout, cwd
            )
            wall_t = time.time() - t0
            n_run += 1

            if success:
                drift, std = compute_drift_metrics(csv_dir)
                if drift is not None:
                    all_results[key] = drift
                    if std is not None:
                        all_std_results[key] = std
                    _write_row(alpha, beta, drift, std, wall_t, 'ok')
                    _update_best(alpha, beta, drift)
                    bstr = (f"  → drift={drift:.6e}%  std={std:.6e}%  wall={wall_t:.1f}s"
                            f"  当前最优: α={best['alpha']:.4f} β={best['beta']:.4f}"
                            f" drift={best['drift']:.6e}%")
                    print(bstr, flush=True)
                else:
                    _write_row(alpha, beta, None, None, wall_t, 'run_ok_no_csv')
                    print(f"  → 运行成功但未找到 CSV: {csv_dir}", flush=True)
            else:
                _write_row(alpha, beta, None, None, wall_t, 'run_failed')

    # ------------------------------------------------------------------
    # 最终汇总
    # ------------------------------------------------------------------
    print(f"\n{'='*65}")
    print(f"扫描完成！{n_total} 个组合（实际运行 {n_run}，跳过 {n_skipped}）")
    print(f"汇总结果: {results_csv_path}")

    if best['alpha'] is not None:
        print(f"\n★ 最优参数 ★")
        print(f"  lyap_alpha = {best['alpha']:.6f}")
        print(f"  lyap_beta  = {best['beta']:.6f}")
        print(f"  Relative Drift = {best['drift']:.8e} %")

        # 保存最优参数 JSON
        best_json_path = output_dir / f"best_params_{timestamp}.json"
        with open(best_json_path, 'w') as f:
            json.dump({
                'lyap_alpha': best['alpha'],
                'lyap_beta':  best['beta'],
                'relative_drift_%': best['drift'],
                'sweep_duration': dur_actual,
                'dt': dt_base,
                'q_init_0': q_init_0,
                'params_file': str(params_file),
                'n_total': n_total,
                'n_run': n_run,
                'n_skipped': n_skipped,
                'timestamp': timestamp,
            }, f, indent=2)
        print(f"最优参数已保存至: {best_json_path}")

        # 打印 yaml 片段供直接粘贴
        print(f"\n将以下内容粘贴到 vi_params.yaml 的 c_atsvi_node 节中：")
        print(f"  c_atsvi_node:")
        print(f"    ros__parameters:")
        print(f"      lyap_alpha: {best['alpha']}")
        print(f"      lyap_beta:  {best['beta']}")

    print(f"{'='*65}\n")

    # ------------------------------------------------------------------
    # 热力图
    # ------------------------------------------------------------------
    if (args.plot or True) and all_results:
        save_path = plot_heatmap(alphas, betas, all_results, output_dir, timestamp,
                                 std_results=all_std_results or None, ref_std=ref_std)
        if args.plot and save_path:
            import matplotlib.pyplot as plt
            plt.show()

    return 0


if __name__ == '__main__':
    sys.exit(main())
