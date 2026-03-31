# Dynamic Workspace (ROS2)

A ROS2 workspace for W10 manipulator variational integrator-based simulation and control.

## Overview

This workspace integrates:
- **w10_sim**: W10 manipulator continuous-time variational integrator with automatic differentiation
- **w10_moveit_kinematics**: MoveIt integration for W10 kinematics and motion planning
- **vi**: 1-DOF variational integrator (submodule)
- **vi_2p**: 2-DOF variational integrator (submodule)

## Quick Start

### Prerequisites
- Ubuntu 22.04 with ROS2 Humble
- Pinocchio and CppAD libraries
- Colcon build system

### Build
```bash
cd ~/ros2_ws/dynamic_ws
colcon build --packages-select w10_sim
source install/setup.bash
```

### Run Simulation
Using launch file (recommended):
```bash
ros2 launch w10_sim ctsvi_w10.launch.py
```

Or with command-line parameters:
```bash
ros2 run w10_sim ctsvi_w10_node --ros-args -p duration:=5.0 -p timestep:=0.01
```

### Analyze Results
```bash
python3 src/w10_sim/scripts/analyze_vi_results.py --path src/w10_sim/csv/q0p2_dt0p01_T10_a0_b0/ctsvi_w10/
```

## Project Structure

```
dynamic_ws/
├── src/
│   ├── vi/                      # 1-DOF variational integrator (submodule)
│   ├── vi_2p/                   # 2-DOF variational integrator (submodule)
│   ├── w10_sim/                 # W10 manipulator simulation
│   └── w10_moveit_kinematics/   # MoveIt integration
├── build/                        # Build artifacts
├── install/                      # Installation outputs
└── log/                          # Build logs
```

## Configuration

Edit `src/w10_sim/config/vi_params.yaml` to modify:
- Initial joint configuration (`q_init`)
- Timestep (`timestep`)
- Simulation duration (`duration`)
- URDF model path (`urdf_path`)

## License

See individual package licenses.
