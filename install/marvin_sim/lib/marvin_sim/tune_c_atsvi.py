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


def compute_relative_drift(csv_dir: Path) -> float | None:
    """
    计算相对能量漂移（单位 %）。
    = max|ΔE| / max|E| × 100，与 analyze_vi_results.py 中的定义一致。
    失败或数据不足时返回 None。
    """
    energy_file = csv_dir / "energy_history.csv"
    if not energy_file.exists():
        return None
    try:
        energy = np.loadtxt(energy_file)
        if energy.ndim == 0 or len(energy) < 2:
            return None
        delta = energy - energy[0]
        max_drift = np.max(np.abs(delta))
        max_e = np.max(np.abs(energy))
        if max_e < 1e-15:
            return None
        return float(max_drift / max_e * 100.0)
    except Exception:
        return None


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


# ---------------------------------------------------------------------------
# 热力图
# ---------------------------------------------------------------------------

def plot_heatmap(alphas: np.ndarray, betas: np.ndarray,
                 results: dict, output_dir: Path, tag: str) -> Path | None:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
    except ImportError:
        print("警告: matplotlib 未安装，跳过热力图绘制")
        return None

    a_step = float(alphas[1] - alphas[0]) if len(alphas) > 1 else 0.05
    b_step = float(betas[1]  - betas[0])  if len(betas)  > 1 else 0.01
    extent = [betas[0]  - b_step * 0.5, betas[-1]  + b_step * 0.5,
              alphas[0] - a_step * 0.5, alphas[-1] + a_step * 0.5]
    Z = np.full((len(alphas), len(betas)), np.nan)
    for i, a in enumerate(alphas):
        for j, b in enumerate(betas):
            key = (round(float(a), 6), round(float(b), 6))
            if key in results:
                Z[i, j] = results[key]

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))

    # --- 子图 1：线性色阶 ---
    ax = axes[0]
    valid = Z[~np.isnan(Z)]
    im = ax.imshow(
        Z, aspect='auto', origin='lower',
        extent=extent,
        cmap='RdYlGn_r',
    )
    plt.colorbar(im, ax=ax, label='Relative Drift [%]')
    ax.set_xlabel('beta')
    ax.set_ylabel('alpha')
    ax.set_title('Relative Energy Drift [%] (linear)')

    # --- 子图 2：对数色阶（更易看出细节）---
    ax2 = axes[1]
    if len(valid) > 0 and valid.min() > 0:
        norm2 = mcolors.LogNorm(vmin=max(valid.min(), 1e-12), vmax=valid.max())
    else:
        norm2 = None
    im2 = ax2.imshow(
        Z, aspect='auto', origin='lower', norm=norm2,
        extent=extent,
        cmap='RdYlGn_r',
    )
    plt.colorbar(im2, ax=ax2, label='Relative Drift [%] (log)')
    ax2.set_xlabel('beta')
    ax2.set_ylabel('alpha')
    ax2.set_title('Relative Energy Drift [%] (log scale)')

    # 标注最优点
    if len(valid) > 0:
        bi, bj = np.unravel_index(np.nanargmin(Z), Z.shape)
        label_str = f"Best: α={alphas[bi]:.4f} β={betas[bj]:.4f}\ndrift={Z[bi,bj]:.4e}%"
        for ax_ in axes:
            ax_.scatter(betas[bj], alphas[bi], c='cyan', s=250, marker='*',
                        zorder=5, label=label_str)
            ax_.legend(fontsize=9)

    fig.suptitle('c_atsvi Lyapunov Gain Sweep — Relative Energy Drift', fontsize=14)
    plt.tight_layout()

    save_path = output_dir / f"heatmap_{tag}.png"
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"热力图已保存至: {save_path}")
    return save_path


# ---------------------------------------------------------------------------
# 从 CSV 结果文件重建 results dict（用于 --plot-only）
# ---------------------------------------------------------------------------

def load_results_csv(results_csv: Path) -> tuple[dict, np.ndarray, np.ndarray]:
    results = {}
    with open(results_csv, newline='') as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            try:
                a = round(float(row['alpha']), 6)
                b = round(float(row['beta']), 6)
                d_str = row.get('relative_drift_%', '')
                if d_str and d_str not in ('FAILED', ''):
                    results[(a, b)] = float(d_str)
            except (ValueError, KeyError):
                pass

    if not results:
        return results, np.array([]), np.array([])

    alphas = sorted(set(k[0] for k in results))
    betas  = sorted(set(k[1] for k in results))
    return results, np.array(alphas), np.array(betas)


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

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # --plot-only 模式：只重绘热力图
    # ------------------------------------------------------------------
    if args.plot_only:
        results_csv = Path(args.plot_only)
        if not results_csv.exists():
            print(f"ERROR: 找不到结果文件 {results_csv}", file=sys.stderr)
            return 1
        results, alphas, betas = load_results_csv(results_csv)
        if not results:
            print("ERROR: 结果文件为空或格式错误", file=sys.stderr)
            return 1
        tag = results_csv.stem
        output_dir = results_csv.parent
        best_key = min(results, key=results.get)
        print(f"\n从 {results_csv} 加载了 {len(results)} 条结果")
        print(f"最优参数: alpha={best_key[0]:.4f}  beta={best_key[1]:.4f}"
              f"  drift={results[best_key]:.6e} %")
        plot_heatmap(alphas, betas, results, output_dir, tag)
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
    all_results: dict[tuple, float] = {}   # (alpha, beta) -> drift %
    best = {'alpha': None, 'beta': None, 'drift': float('inf')}

    n_skipped = 0   # 因 resume 跳过的数量
    n_run     = 0   # 实际运行的数量
    t_run_start = time.time()  # 仅统计实际运行的耗时

    with open(results_csv_path, 'w', newline='') as results_fp:
        writer = csv.writer(results_fp)
        writer.writerow(['alpha', 'beta', 'relative_drift_%', 'wall_time_s', 'status'])
        results_fp.flush()

        def _write_row(a, b, drift_val, wall_t, status):
            drift_str = f"{drift_val:.10f}" if drift_val is not None else 'FAILED'
            writer.writerow([f"{a}", f"{b}", drift_str, f"{wall_t:.1f}", status])
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
                drift = compute_relative_drift(csv_dir)
                if drift is not None:
                    all_results[key] = drift
                    _write_row(alpha, beta, drift, 0.0, 'resume_from_csv')
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
                drift = compute_relative_drift(csv_dir)
                if drift is not None:
                    all_results[key] = drift
                    _write_row(alpha, beta, drift, wall_t, 'ok')
                    _update_best(alpha, beta, drift)
                    bstr = (f"  → drift={drift:.6e}%  wall={wall_t:.1f}s"
                            f"  当前最优: α={best['alpha']:.4f} β={best['beta']:.4f}"
                            f" drift={best['drift']:.6e}%")
                    print(bstr, flush=True)
                else:
                    _write_row(alpha, beta, None, wall_t, 'run_ok_no_csv')
                    print(f"  → 运行成功但未找到 CSV: {csv_dir}", flush=True)
            else:
                _write_row(alpha, beta, None, wall_t, 'run_failed')

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
        save_path = plot_heatmap(alphas, betas, all_results, output_dir, timestamp)
        if args.plot and save_path:
            import matplotlib.pyplot as plt
            plt.show()

    return 0


if __name__ == '__main__':
    sys.exit(main())
