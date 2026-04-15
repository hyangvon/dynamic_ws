#!/usr/bin/env python3
"""
从 CSV 数据按原始仿真时间在 RViz 中回放机械臂姿态。

用法：
    # 指定 csv 子目录（包含 q_history.csv 和 time_history.csv）
    ros2 run marvin_sim replay_rviz.py --path src/marvin_sim/csv/q0_dt0p01_T10_a0p4_b0p04/ctsvi_ad/

    # 倍速回放（2x）
    ros2 run marvin_sim replay_rviz.py --path <dir> --speed 2.0

    # 循环播放
    ros2 run marvin_sim replay_rviz.py --path <dir> --loop
"""

import argparse
import sys
import time
import os
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


JOINT_NAMES = [
    'Joint1', 'Joint2', 'Joint3',
    'Joint4', 'Joint5', 'Joint6', 'Joint7',
]


def find_latest_ctsvi_dir(base='src/marvin_sim/csv'):
    """返回最新修改的 ctsvi_ad 子目录（若未指定 --path 时使用）。"""
    candidates = []
    base_path = base
    if not os.path.isdir(base_path):
        return None
    for root, dirs, files in os.walk(base_path):
        if 'q_history.csv' in files and 'time_history.csv' in files:
            candidates.append(root)
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def load_csv(path):
    return np.loadtxt(path, delimiter=',')


class ReplayNode(Node):
    def __init__(self, q_data, t_data, joint_names, speed, loop):
        super().__init__('replay_rviz')
        self._pub = self.create_publisher(JointState, 'joint_states', 10)
        self._q = q_data          # shape (N, nq)
        self._t = t_data          # shape (N,)
        self._names = joint_names
        self._speed = speed
        self._loop = loop
        self._idx = 0
        self._wall_start = None
        self._sim_start = float(self._t[0])

        nq = self._q.shape[1]
        # 如果 CSV 列数与 JOINT_NAMES 不一致，截断或补全名称
        if nq < len(self._names):
            self._names = self._names[:nq]
        elif nq > len(self._names):
            for i in range(len(self._names), nq):
                self._names.append(f'joint_{i+1}')

        self.get_logger().info(
            f'Replay: {len(self._t)} frames, '
            f'duration={self._t[-1]-self._t[0]:.2f}s, '
            f'speed={self._speed}x, loop={self._loop}'
        )

        # 使用 wall-clock 定时器，分辨率约 1 ms
        self._timer = self.create_timer(0.005, self._tick)

    def _tick(self):
        now_wall = time.monotonic()
        if self._wall_start is None:
            self._wall_start = now_wall

        # 当前模拟时刻
        sim_now = self._sim_start + (now_wall - self._wall_start) * self._speed

        # 前进到最近的帧
        while self._idx < len(self._t) - 1 and self._t[self._idx + 1] <= sim_now:
            self._idx += 1

        if self._idx >= len(self._t) - 1:
            # 播放完毕 — 最后一帧仍发布一次
            self._publish(self._idx)
            if self._loop:
                self.get_logger().info('Loop: restarting playback.')
                self._idx = 0
                self._wall_start = time.monotonic()
                self._sim_start = float(self._t[0])
            else:
                self.get_logger().info('Replay finished.')
                self._timer.cancel()
            return

        self._publish(self._idx)

    def _publish(self, idx):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self._names
        msg.position = self._q[idx].tolist()
        self._pub.publish(msg)


def main():
    parser = argparse.ArgumentParser(
        description='在 RViz 中按真实时间回放仿真 CSV 数据'
    )
    parser.add_argument(
        '--path', '-p', default=None,
        help='包含 q_history.csv 和 time_history.csv 的目录，默认自动选最新'
    )
    parser.add_argument(
        '--speed', '-s', type=float, default=1.0,
        help='回放倍速（默认 1.0）'
    )
    parser.add_argument(
        '--loop', '-l', action='store_true',
        help='循环播放'
    )
    # 忽略 ros2 run 透传的 ROS 参数
    args, _ = parser.parse_known_args()

    csv_dir = args.path
    if csv_dir is None:
        csv_dir = find_latest_ctsvi_dir()
        if csv_dir is None:
            print('[ERROR] 未找到 CSV 目录，请用 --path 指定。', file=sys.stderr)
            sys.exit(1)
        print(f'[INFO] 自动选择最新目录: {csv_dir}')

    q_file = os.path.join(csv_dir, 'q_history.csv')
    t_file = os.path.join(csv_dir, 'time_history.csv')

    if not os.path.isfile(q_file) or not os.path.isfile(t_file):
        print(f'[ERROR] 未在 {csv_dir} 中找到 q_history.csv 或 time_history.csv',
              file=sys.stderr)
        sys.exit(1)

    q_data = load_csv(q_file)
    t_data = load_csv(t_file)

    if q_data.ndim == 1:
        q_data = q_data.reshape(-1, 1)

    if q_data.shape[0] != t_data.shape[0]:
        # 对齐行数（取较短者）
        n = min(q_data.shape[0], t_data.shape[0])
        q_data = q_data[:n]
        t_data = t_data[:n]

    rclpy.init()
    node = ReplayNode(q_data, t_data, list(JOINT_NAMES), args.speed, args.loop)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
