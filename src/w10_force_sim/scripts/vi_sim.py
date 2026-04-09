#!/usr/bin/env python3
import subprocess
import sys
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
try:
    import yaml
except Exception:
    yaml = None

def run_ctsvi():
    """运行 C++ 仿真节点"""
    config_file = os.path.expanduser('~/ros2_ws/dynamic_ws/src/w10_force_sim/config/vi_params.yaml')

    print("Starting ctsvi simulation...")

    try:
        result = subprocess.run([
            'ros2', 'run', 'w10_force_sim', 'ctsvi_ad_node',
            '--ros-args', '--params-file', config_file
        ], check=True)

        print("Simulation completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Simulation failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def run_atsvi():
    """运行 C++ 仿真节点"""
    config_file = os.path.expanduser('~/ros2_ws/dynamic_ws/src/w10_force_sim/config/vi_params.yaml')

    print("Starting atsvi simulation...")

    try:
        result = subprocess.run([
            'ros2', 'run', 'w10_force_sim', 'atsvi_ad_node',
            '--ros-args', '--params-file', config_file
        ], check=True)

        print("Simulation completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Simulation failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def run_etsvi():
    """运行 C++ 仿真节点"""
    config_file = os.path.expanduser('~/ros2_ws/dynamic_ws/src/w10_force_sim/config/vi_params.yaml')

    print("Starting etsvi simulation...")

    try:
        result = subprocess.run([
            'ros2', 'run', 'w10_force_sim', 'etsvi_node',
            '--ros-args', '--params-file', config_file
        ], check=True)

        print("Simulation completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Simulation failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-sim', action='store_true', help='Skip running simulations and only plot using existing CSVs')
    args = parser.parse_args()

    # 运行仿真（除非用户要求跳过）
    if not args.skip_sim:
        if not run_ctsvi():
            return 1

        # if not run_atsvi():
        #     return 1

        # if not run_etsvi():
        #     return 1

    print("All tasks completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
